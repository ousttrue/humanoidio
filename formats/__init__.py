from typing import Tuple
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


def parse_gltf(path: pathlib.Path) -> Tuple[gltf.glTF, bytes]:
    '''
    parse gltf or glb
    '''
    with path.open('rb') as f:
        ext = path.suffix.lower()
        if ext == '.gltf':
            parsed = gltf.glTF.from_dict(json.load(f))
            return parsed, b''
        elif ext == '.glb' or ext == '.vrm':
            glb_parsed = glb.Glb.from_bytes(f.read())
            parsed = gltf.glTF.from_dict(json.loads(glb_parsed.json))
            return parsed, glb_parsed.bin
        else:
            raise Exception(f'{ext} is not supported')
