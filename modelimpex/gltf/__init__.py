import pathlib
from typing import Tuple, Dict, Any
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

    def set_attribute(self, key: str, value):
        if key == 'POSITION':
            self.POSITION = value
        elif key == 'NORMAL':
            self.NORMAL = value
        elif key == 'TEXCOORD_0':
            self.TEXCOORD_0 = value


class Mesh:
    def __init__(self):
        self.submeshes = []


class Loader:
    def __init__(self, gltf: Dict[str, Any], bin: bytes = None):
        self.gltf = gltf
        self.bin = bin
        self.meshes = []

    def get_accessor(self, index: int):
        return self.gltf['accessors'][index]

    def load(self):
        for m in self.gltf['meshes']:
            mesh = Mesh()
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

    loader = Loader(gltf, json_chunk)
    loader.load()
    return loader


def load(src: pathlib.Path):
    if src.suffix == '.gltf':
        return load_gltf(src)
    else:
        return load_glb(src)
