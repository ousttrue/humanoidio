from lib.bpy_helper import scan
import unittest
import os
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore
VRM_SAMPLE_DIR = pathlib.Path(os.getenv('VRM_SAMPLES'))  # type: ignore
import bpy
from lib import formats, pyscene, bpy_helper
from tests import helper


class BpyTests(unittest.TestCase):
    '''
    gltf(glb, vrm) -> pyscene -> bpy -> pyscene
    '''
    def test_box_textured_glb(self):
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF-Binary/BoxTextured.glb'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)

        bpy_helper.load(bpy.context, roots)
        scanner = bpy_helper.scan()

        exported = pyscene.to_gltf(scanner.nodes)
        self.assertTrue(helper.check_gltf(data, exported))
