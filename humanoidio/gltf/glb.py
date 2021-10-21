from typing import Tuple, Dict, Any
import json
import io

GLB_MAGIC = int.to_bytes(0x46546C67, length=4, byteorder='little')
GLB_VERSION = int.to_bytes(2, length=4, byteorder='little')
JSON_CHUNK_MAGIC = int.to_bytes(0x4E4F534A, length=4, byteorder='little')
BIN_CHUNK_MAGIC = int.to_bytes(0x004E4942, length=4, byteorder='little')


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

    def read_chunk(self) -> Tuple[bytes, bytes]:
        chunk_length = self.read_bytes(4)
        chunk_type = self.read_bytes(4)
        chunk_body = self.read_bytes(
            int.from_bytes(chunk_length, byteorder='little'))
        return (chunk_type, chunk_body)


def get_glb_chunks(data: bytes) -> Tuple[bytes, bytes]:
    reader = ByteReader(data)

    magic = reader.read_bytes(4)
    if magic != GLB_MAGIC:
        raise ValueError('invalid magic')

    version = reader.read_bytes(4)
    if version != GLB_VERSION:
        raise ValueError(f'unknown version: {version} != 2')

    length = reader.read_int32()

    chunk_type, chunk_body = reader.read_chunk()
    if chunk_type != JSON_CHUNK_MAGIC:
        raise ValueError(f'first chunk: {chunk_type:x} != 0x4E4F534A')
    json_chunk = chunk_body

    chunk_type, chunk_body = reader.read_chunk()
    if chunk_type != BIN_CHUNK_MAGIC:
        raise ValueError(f'second chunk: {chunk_type:x} != 0x004E4942')
    bin_chunk = chunk_body

    while length < reader.pos:
        # chunk_type, chunk_body = reader.read_chunk()
        raise NotImplementedError()

    return (json_chunk, bin_chunk)


def to_glb(gltf: Dict[str, Any], bin: bytes):

    with io.BytesIO() as bs:
        json_body = json.dumps(gltf).encode('utf-8')

        # header
        bs.write(GLB_MAGIC)
        bs.write(GLB_VERSION)
        bs.write(
            int.to_bytes(12 + (8 + len(json_body)) + (8 + len(bin)),
                         length=4,
                         byteorder='little'))

        # JSON chunk
        bs.write(int.to_bytes(len(json_body), length=4, byteorder='little'))
        bs.write(JSON_CHUNK_MAGIC)
        bs.write(json_body)

        # BIN chunk
        bs.write(int.to_bytes(len(bin), length=4, byteorder='little'))
        bs.write(BIN_CHUNK_MAGIC)
        bs.write(bin)

        return bs.getvalue()
