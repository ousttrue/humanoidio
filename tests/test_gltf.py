import unittest
import os
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore

from lib import import_submesh
from lib.formats import parse_gltf
from lib.yup.submesh_mesh import SubmeshMesh


class Test_TestIncrementDecrement(unittest.TestCase):
    def test_box(self):
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = import_submesh(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        self.assertEqual(len(mesh.positions), 24)


if __name__ == '__main__':
    unittest.main()
