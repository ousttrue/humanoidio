from typing import NamedTuple, IO, Any
import struct


class BinaryReader:
    def __init__(self, src: bytes):
        self.data = src
        self.pos = 0

    def int32(self) -> int:
        value = struct.unpack('i', self.data[self.pos:self.pos + 4])
        self.pos += 4
        return value[0]

    def bytes(self, length: int) -> bytes:
        value = self.data[self.pos:self.pos + length]
        self.pos += length
        return value


class Glb(NamedTuple):
    json: bytes
    bin: bytes

    @staticmethod
    def from_bytes(src: bytes) -> 'Glb':
        r = BinaryReader(src)
        magic = r.bytes(4)
        if magic != b'glTF':
            raise Exception()
        version = r.int32()
        if version != 2:
            raise Exception()
        length = r.int32() - 12
        json_bytes = b''
        bin_bytes = b''
        while length > 0:
            chunk_length = r.int32()
            length -= 4
            chunk_type = r.bytes(4)
            length -= 4
            if chunk_type == b'JSON':
                json_bytes = r.bytes(chunk_length)
            elif chunk_type == b'BIN\0':
                bin_bytes = r.bytes(chunk_length)
            else:
                raise Exception()
            length -= chunk_length
        return Glb(json_bytes, bin_bytes)

    def write_to(self, w: IO[Any]) -> None:
        json_bytes = self.json
        if len(json_bytes) % 4 != 0:
            json_padding_size = (4 - len(json_bytes) % 4)
            print(f'add json_padding_size: {json_padding_size}')
            json_bytes += b' ' * json_padding_size
        json_header = struct.pack(b'I', len(json_bytes)) + b'JSON'
        bin_header = struct.pack(b'I', len(self.bin)) + b'BIN\x00'
        header = b'glTF' + struct.pack(
            'II', 2, 12 + len(json_header) + len(json_bytes) +
            len(bin_header) + len(self.bin))
        #
        w.write(header)
        w.write(json_header)
        w.write(json_bytes)
        w.write(bin_header)
        w.write(self.bin)
