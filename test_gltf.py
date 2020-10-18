import unittest
import os
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore

from lib.formats.gltf import glTF
from lib.formats import parse_gltf
from lib import import_submesh


class Test_TestIncrementDecrement(unittest.TestCase):
    def test_box(self):
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = import_submesh(data)
        self.assertEqual(len(roots), 1)


if __name__ == '__main__':
    unittest.main()
