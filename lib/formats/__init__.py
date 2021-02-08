import pathlib
import json
from .generated import gltf
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


import json
from json import JSONEncoder
import re


class ComplexEncoder(json.JSONEncoder):
    def isinstance(self, obj, cls):
        return isinstance(obj, list)

    def default(self, obj):
        def is_num(n) -> bool:
            return isinstance(n, int) or isinstance(n, float)

        if isinstance(obj, list) and all(is_num(x) for x in obj):
            return '[' + ', '.join(obj)  + ']'

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def to_json(d: dict) -> str:
    return json.dumps(d, indent=2, cls=ComplexEncoder)
