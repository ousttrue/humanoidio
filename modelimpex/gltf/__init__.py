from logging import getLogger

logger = getLogger(__name__)

import pathlib
from typing import Tuple, Dict, Any, List, Generator
import json


class ByteReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read_bytes(self, read_len: int) -> bytes:
        if self.pos + read_len > len(self.data):
            raise IndexError()
        value = self.data[self.pos:self.pos + read_len]
        self.pos += read_len
        return value

    def read_int32(self) -> int:
        value = self.read_bytes(4)
        return int.from_bytes(value, byteorder='little')

    def read_chunk(self) -> Tuple[int, bytes]:
        chunk_length = self.read_int32()
        chunk_type = self.read_int32()
        chunk_body = self.read_bytes(chunk_length)
        return (chunk_type, chunk_body)


def load_gltf(src: pathlib.Path):
    raise NotImplementedError()


def get_glb_chunks(data: bytes) -> Tuple[bytes, bytes]:
    reader = ByteReader(data)

    magic = reader.read_int32()
    if magic != 0x46546C67:
        raise ValueError('invalid magic')

    version = reader.read_int32()
    if version != 2:
        raise ValueError(f'unknown version: {version} != 2')

    length = reader.read_int32()

    chunk_type, chunk_body = reader.read_chunk()
    if chunk_type != 0x4E4F534A:
        raise ValueError(f'first chunk: {chunk_type:x} != 0x4E4F534A')
    json_chunk = chunk_body

    chunk_type, chunk_body = reader.read_chunk()
    if chunk_type != 0x004E4942:
        raise ValueError(f'second chunk: {chunk_type:x} != 0x004E4942')
    bin_chunk = chunk_body

    while length < reader.pos:
        chunk_type, chunk_body = reader.read_chunk()

    return (json_chunk, bin_chunk)


class Submesh:
    def __init__(self):
        self.indices = None
        self.POSITION = None
        self.NORMAL = None
        self.TEXCOORD_0 = None
        self.JOINTS_0 = None
        self.WEIGHTS_0 = None

    def set_attribute(self, key: str, value):
        if key == 'POSITION':
            self.POSITION = value
        elif key == 'NORMAL':
            self.NORMAL = value
        elif key == 'TEXCOORD_0':
            self.TEXCOORD_0 = value
        elif key == 'JOINTS_0':
            self.JOINTS_0 = value
        elif key == 'WEIGHTS_0':
            self.WEIGHTS_0 = value
        else:
            raise NotImplementedError()

    def get_vertices(self):
        pos = self.POSITION()
        nom = self.NORMAL()
        while True:
            try:
                p = next(pos)
                n = next(nom)
                yield p, n
            except StopIteration:
                break

    def get_indices(self):
        i = self.indices()
        while True:
            try:
                i0 = next(i)
                i1 = next(i)
                i2 = next(i)
                yield (i0, i1, i2)
            except StopIteration:
                break


class Mesh:
    def __init__(self, name: str):
        self.name = name
        self.submeshes = []


def get_span(data: bytes, accessor):
    ct = accessor['componentType']
    t = accessor['type']
    count = accessor['count']
    if ct == 5120:
        # int8
        if t == "SCALAR":

            def int8():
                for x in data[:count]:
                    yield x

            return int8
        else:
            raise NotImplementedError()
    elif ct == 5121:
        # uint8
        if t == "SCALAR":

            def uint8():
                for x in memoryview(data[:count]).cast('B'):
                    yield x

            return uint8
        else:
            raise NotImplementedError()
    elif ct == 5122:
        # int16
        if t == "SCALAR":

            def int16():
                for x in memoryview(data[:count * 2]).cast('h'):
                    yield x

            return int16
        else:
            raise NotImplementedError()
    elif ct == 5123:
        # uint16
        if t == "SCALAR":

            def uint16():
                for x in memoryview(data[:count * 2]).cast('H'):
                    yield x

            return uint16
        elif t == "VEC4":

            def ushort4():
                it = iter(memoryview(data[:count * 2 * 4]).cast('H'))
                while True:
                    try:
                        u0 = next(it)
                        u1 = next(it)
                        u2 = next(it)
                        u3 = next(it)
                        yield u0, u1, u2, u3
                    except StopIteration:
                        break

            return ushort4

        else:
            raise NotImplementedError()
    elif ct == 5125:
        # uint32
        if t == "SCALAR":

            def uint32():
                for x in memoryview(data[:count * 4]).cast('I'):
                    yield x

            return uint32
        else:
            raise NotImplementedError()
    elif ct == 5126:
        # float
        if t == 'VEC4':

            def float4():
                it = iter(memoryview(data[:count * 4 * 4]).cast('f'))
                while True:
                    try:
                        f0 = next(it)
                        f1 = next(it)
                        f2 = next(it)
                        f3 = next(it)
                        yield (f0, f1, f2, f3)
                    except StopIteration:
                        break

            return float4
        elif t == 'VEC3':

            def float3():
                it = iter(memoryview(data[:count * 4 * 3]).cast('f'))
                while True:
                    try:
                        f0 = next(it)
                        f1 = next(it)
                        f2 = next(it)
                        yield (f0, f1, f2)
                    except StopIteration:
                        break

            return float3
        elif t == 'VEC2':

            def float2():
                it = iter(memoryview(data[:count * 4 * 2]).cast('f'))
                while True:
                    try:
                        f0 = next(it)
                        f1 = next(it)
                        yield (f0, f1)
                    except StopIteration:
                        break

            return float2
        else:
            raise NotImplementedError()
    else:
        raise ValueError(f'unknown component type: {ct}')


class Loader:
    def __init__(self, gltf: Dict[str, Any], bin: bytes = None):
        self.gltf = gltf
        self.bin = bin
        self.meshes: List[Mesh] = []

    def get_accessor(self, index: int):
        accessor = self.gltf['accessors'][index]
        bufferView_index = accessor['bufferView']
        bufferView = self.gltf['bufferViews'][bufferView_index]
        accessor_offset = accessor['byteOffset']
        if self.bin:
            offset = bufferView['byteOffset'] + accessor_offset
            length = bufferView['byteLength']
            slice = self.bin[offset:offset + length]
            span = get_span(slice, accessor)
            return span
        else:
            raise NotImplementedError('without bin')

    def load(self):
        for i, m in enumerate(self.gltf['meshes']):
            mesh = Mesh(m.get('name', f'mesh{i}'))
            self.meshes.append(mesh)

            for prim in m['primitives']:
                sm = Submesh()
                mesh.submeshes.append(sm)
                for k, v in prim['attributes'].items():
                    sm.set_attribute(k, self.get_accessor(v))
                sm.indices = self.get_accessor(prim['indices'])


def load_glb(src: pathlib.Path) -> Loader:
    json_chunk, bin_chunk = get_glb_chunks(src.read_bytes())
    gltf = json.loads(json_chunk)

    loader = Loader(gltf, bin_chunk)
    loader.load()
    return loader


def load(src: pathlib.Path):
    if src.suffix == '.gltf':
        return load_gltf(src)
    else:
        return load_glb(src)
