from logging import getLogger

logger = getLogger(__name__)

import os
import sys

import pathlib
import unittest
from logging import basicConfig, DEBUG

HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_KEY = 'GLTF_SAMPLE_MODELS'
GLTF_SAMPLE_DIR = pathlib.Path(os.environ[GLTF_SAMPLE_KEY]) / '2.0'
GLTF_PATH = GLTF_SAMPLE_DIR / 'BoxTextured/glTF-Binary/BoxTextured.glb'
VRM_SAMPLE_KEY = 'VRM_SAMPLES'
VRM_SAMPLE_DIR = pathlib.Path(os.environ[VRM_SAMPLE_KEY])
VRM_PATH = VRM_SAMPLE_DIR / 'vroid/Darkness_Shibu.vrm'

basicConfig(
    level=DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

import bpy


def clear():
    # clear scene
    bpy.ops.object.select_all(action='SELECT')  # type: ignore
    bpy.ops.object.delete()

    # only worry about data in the startup scene
    for bpy_data_iter in (
            bpy.data.objects,
            bpy.data.meshes,
            bpy.data.lights,
            bpy.data.cameras,
            bpy.data.materials,
    ):
        for id_data in bpy_data_iter:
            # id_data.user_clear();
            bpy_data_iter.remove(id_data)


class TestBpy(unittest.TestCase):
    def test_box_textured_glb(self):
        self.assertTrue(GLTF_PATH.exists())

        # clear scene
        clear()

        import modelimpex
        modelimpex.register()

        bpy.ops.modelimpex.importer(filepath=str(VRM_PATH))  # type: ignore

        # modelimpex.scene.load(path)
        # data = formats.parse_gltf(path)
        # index_map = pyscene.load(data)
        # roots = index_map.get_roots()
        # self.assertEqual(roots[0].children[0].mesh.attributes.position[0],
        #                  Float3(-0.5, -0.5, 0.5))

        # bpy_helper.importer.load(bpy.context.scene.collection, index_map)
        # exported = bpy_helper.exporter.scan()
        # self.assertEqual(exported.nodes[1].mesh.positions[0],
        #                  Float3(-0.5, -0.5, -0.5))

        # exported = [node for node in exported.nodes if not node.parent]
        # self.assertEqual(len(roots), len(exported))
        # for l, r in zip(roots, exported):
        #     self._check_node(l, r)

        bpy.ops.wm.save_as_mainfile(filepath=str(HERE.parent / 'tmp.blend'))
        modelimpex.unregister()


if __name__ == "__main__":
    unittest.main()
