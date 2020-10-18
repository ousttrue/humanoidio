import unittest
import os
import json
import pathlib
import sys
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore
sys.path.append(str(HERE.parent))
from formats.gltf import glTF


class Test_TestIncrementDecrement(unittest.TestCase):
    def test_box(self):
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
        self.assertTrue(path.exists())

        gltf_json = json.loads(path.read_text())
        parsed = glTF.from_dict(gltf_json)
        self.assertEqual(parsed.asset.version, '2.0')
        


if __name__ == '__main__':
    unittest.main()
