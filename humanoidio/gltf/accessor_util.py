import ctypes
from enum import IntEnum
from typing import Iterable, Any, Dict, Generator
from .coordinate import (Coodinate, Conversion)
from .types import Float3


def enumerate_1(iterable) -> Generator[Any, None, None]:
    def g():
        for x in iterable:
            yield x

    return g


def enumerate_2(iterable) -> Generator[Any, None, None]:
    def g():
        it = iter(iterable)
        while True:
            try:
                _0 = next(it)
                _1 = next(it)
                yield (_0, _1)
            except StopIteration:
                break

    return g


def enumerate_3(iterable) -> Generator[Any, None, None]:
    def g():
        it = iter(iterable)
        while True:
            try:
                _0 = next(it)
                _1 = next(it)
                _2 = next(it)
                yield (_0, _1, _2)
            except StopIteration:
                break

    return g


def enumerate_4(iterable) -> Generator[Any, None, None]:
    def g():
        it = iter(iterable)
        while True:
            try:
                _0 = next(it)
                _1 = next(it)
                _2 = next(it)
                _3 = next(it)
                yield (_0, _1, _2, _3)
            except StopIteration:
                break

    return g


class ComponentType(IntEnum):
    Int8 = 5120
    UInt8 = 5121
    Int16 = 5122
    UInt16 = 5123
    UInt32 = 5125
    Float = 5126


def get_span(data: bytes, ct: ComponentType) -> Iterable[Any]:
    if ct == ComponentType.Int8:
        return memoryview(data).cast('b')
    elif ct == ComponentType.UInt8:
        return memoryview(data).cast('B')
    elif ct == ComponentType.Int16:
        return memoryview(data).cast('h')
    elif ct == ComponentType.UInt16:
        return memoryview(data).cast('H')
    elif ct == ComponentType.UInt32:
        return memoryview(data).cast('I')
    elif ct == ComponentType.Float:
        return memoryview(data).cast('f')
    else:
        raise ValueError(f'unknown component type: {ct}')


CT_SIZE_MAP = {
    ComponentType.Int8: 1,
    ComponentType.UInt8: 1,
    ComponentType.Int16: 2,
    ComponentType.UInt16: 2,
    ComponentType.UInt32: 4,
    ComponentType.Float: 4,
}

TYPE_SIZE_MAP = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


def get_size_count(accessor):
    ct = accessor['componentType']
    t = accessor['type']
    return (CT_SIZE_MAP[ComponentType(ct)], TYPE_SIZE_MAP[t])


class GltfAccessor:
    def __init__(self, gltf: Dict[str, Any], bin: bytes, dst: Coodinate):
        self.gltf = gltf
        self.bin = bin
        self.conversion = Conversion(Coodinate.GLTF, dst)

    def bufferview_bytes(self, index: int) -> bytes:
        bufferView = self.gltf['bufferViews'][index]
        if self.bin:
            offset = bufferView['byteOffset']
            length = bufferView['byteLength']
            return self.bin[offset:offset + length]
        else:
            raise NotImplementedError('without bin')

    def accessor_generator(self, index: int) -> Generator[Any, None, None]:
        accessor = self.gltf['accessors'][index]
        offset = accessor.get('byteOffset', 0)
        count = accessor.get('count')
        element_size, element_count = get_size_count(accessor)
        data = self.bufferview_bytes(
            accessor['bufferView'])[offset:offset +
                                    element_size * element_count * count]
        span = get_span(data, ComponentType(accessor['componentType']))
        if element_count == 1:
            return enumerate_1(span)
        elif element_count == 2:
            return enumerate_2(span)
        elif element_count == 3:
            return enumerate_3(span)
        elif element_count == 4:
            return enumerate_4(span)
        else:
            raise NotImplementedError()


def get_type_count(values):
    if values._type_ == ctypes.c_uint32:
        return ComponentType.UInt32, 1
    elif values._type_ == Float3:
        return ComponentType.Float, 3
    else:
        raise NotImplementedError(f'{values._type_}')
