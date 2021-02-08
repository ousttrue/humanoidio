from typing import Tuple, NamedTuple, List
import pathlib
import json
from .  import generated
from .glb import Glb


class GltfContext(NamedTuple):
    # parsed glTF
    gltf: generated.glTF
    # bytes of glb binary chunk
    bin: bytes
    # path for file exists
    dir: pathlib.Path

    def get_uri_bytes(self, uri: str) -> bytes:
        path = self.dir / uri
        return path.read_bytes()
