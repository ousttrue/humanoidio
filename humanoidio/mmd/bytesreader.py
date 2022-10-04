from typing import Type
import ctypes
import struct


def bytes_to_str(data: bytes, encoding: str = 'cp932') -> str:
    if encoding in ('cp932', 'utf-8'):
        try:
            zero = data.index(b'\0')
            data = data[:zero]
        except ValueError:
            pass
    if isinstance(data, ctypes.Array):
        data = memoryview(data).tobytes()
    decoded = data.decode(encoding, errors='ignore')

    for i, c in enumerate(decoded):
        if c == '\x00':
            return decoded[:i]

    return decoded


class BytesReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def bytes(self, length: int) -> bytes:
        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data

    def str(self, length: int, encoding: str) -> str:
        data = self.bytes(length)
        return bytes_to_str(data, encoding=encoding)

    def uint8(self) -> int:
        return struct.unpack('B', self.bytes(1))[0]

    def uint16(self) -> int:
        return struct.unpack('H', self.bytes(2))[0]

    def uint32(self) -> int:
        return struct.unpack('I', self.bytes(4))[0]

    def int32(self) -> int:
        return struct.unpack('i', self.bytes(4))[0]

    def float32(self) -> float:
        return struct.unpack('f', self.bytes(4))[0]

    def array(self, array_type: Type[ctypes.Array]) -> ctypes.Array:
        return array_type.from_buffer_copy(self.bytes(ctypes.sizeof(array_type)))

    def struct(self, array_type: Type[ctypes.Structure]) -> ctypes.Structure:
        return array_type.from_buffer_copy(self.bytes(ctypes.sizeof(array_type)))
