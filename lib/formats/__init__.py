import pathlib
import json
from . import gltf_generated as gltf
from .glb import Glb
from .gltf_context import GltfContext
from .bytesreader import BytesReader
from .buffermanager import BufferManager
from .vrm0x import HumanoidBones

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
            glb_parsed = Glb.from_bytes(f.read())
            parsed = gltf.glTF.from_dict(json.loads(glb_parsed.json))
            return GltfContext(parsed, glb_parsed.bin, path.parent)
        else:
            raise Exception(f'{ext} is not supported')
