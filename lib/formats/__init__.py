from typing import Tuple, NamedTuple, List
import pathlib
import json
import importlib
from . import glb
importlib.reload(glb)
from . import gltf
importlib.reload(gltf)
from . import vrm0x
importlib.reload(vrm0x)
from . import binarybuffer
importlib.reload(binarybuffer)
from . import buffermanager
importlib.reload(buffermanager)
from . import buffertypes
importlib.reload(buffertypes)

from ..pyscenetree import Node, SubmeshMesh


class GltfContext(NamedTuple):
    # parsed glTF
    data: gltf.glTF
    # bytes of glb binary chunk
    binary: bytes
    # path for file exists
    dir: pathlib.Path


def parse_gltf(path: pathlib.Path) -> GltfContext:
    '''
    parse gltf or glb
    '''
    with path.open('rb') as f:
        ext = path.suffix.lower()
        if ext == '.gltf':
            parsed = gltf.glTF.from_dict(json.load(f))
            return GltfContext(parsed, b'', path.parent)
        elif ext == '.glb' or ext == '.vrm':
            glb_parsed = glb.Glb.from_bytes(f.read())
            parsed = gltf.glTF.from_dict(json.loads(glb_parsed.json))
            return GltfContext(parsed, glb_parsed.bin, path.parent)
        else:
            raise Exception(f'{ext} is not supported')


def import_submesh(data: GltfContext) -> List[Node]:
    roots = []
    return roots
