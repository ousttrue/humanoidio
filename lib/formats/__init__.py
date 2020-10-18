from typing import Tuple, NamedTuple, List
import pathlib
import json
from .gltf import glTF
from .glb import Glb


class GltfContext(NamedTuple):
    # parsed glTF
    gltf: glTF
    # bytes of glb binary chunk
    bin: bytes
    # path for file exists
    dir: pathlib.Path


def parse_gltf(path: pathlib.Path) -> GltfContext:
    '''
    parse gltf or glb
    '''
    with path.open('rb') as f:
        ext = path.suffix.lower()
        if ext == '.gltf':
            parsed = glTF.from_dict(json.load(f))
            return GltfContext(parsed, b'', path.parent)
        elif ext == '.glb' or ext == '.vrm':
            glb_parsed = Glb.from_bytes(f.read())
            parsed = glTF.from_dict(json.loads(glb_parsed.json))
            return GltfContext(parsed, glb_parsed.bin, path.parent)
        else:
            raise Exception(f'{ext} is not supported')
