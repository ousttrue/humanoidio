from typing import Tuple
import pathlib
from . import pmx_loader


def load(path: pathlib.Path):
    bytes = path.read_bytes()
    return pmx_loader.Pmx(bytes)
