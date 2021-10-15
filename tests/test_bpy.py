import os
import sys

KEY = 'GLTF_SAMPLE_MODELS'
if KEY not in os.environ:
    sys.exit()
import pathlib

HERE = pathlib.Path(__file__).absolute().parent
SAMPLE_DIR = pathlib.Path(os.environ[KEY]) / '2.0'

import unittest

sys.path.append(str(HERE.parent.parent))
print(sys.path)
import modelimpex.lib.scene


class TestBpy(unittest.TestCase):
    def test_box_textured_glb(self):
        path = SAMPLE_DIR / 'BoxTextured/glTF-Binary/BoxTextured.glb'
        self.assertTrue(path.exists())

        modelimpex.lib.scene.load(path)
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


if __name__ == "__main__":
    unittest.main()
