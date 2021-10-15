import os
import sys

KEY = 'GLTF_SAMPLE_MODELS'
if KEY not in os.environ:
    sys.exit()
import pathlib

SAMPLE_DIR = pathlib.Path(os.environ[KEY]) / '2.0'

import unittest
from typing import Optional, Iterable


def get_gltf(d: pathlib.Path) -> Optional[pathlib.Path]:
    if d.is_dir():
        for e in d.iterdir():
            if e.suffix in ('.gltf', '.glb'):
                return e


def iter_gltf(d: pathlib.Path) -> Iterable[pathlib.Path]:
    for model in d.iterdir():
        if model.is_dir():
            for d in model.iterdir():
                if d.name in ('screenshot', 'README.md'):
                    continue
                gltf = get_gltf(d)
                if gltf:
                    yield gltf


class TestGltf(unittest.TestCase):
    def test_load(self):
        for f in iter_gltf(SAMPLE_DIR):
            print(f.relative_to(SAMPLE_DIR))
            self.assertEqual(1, 1)
            break


if __name__ == "__main__":
    unittest.main()
