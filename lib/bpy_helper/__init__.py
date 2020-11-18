from typing import List, Optional
import bpy, mathutils
from .. import pyscene
from .exporter import Exporter
from .importer import Importer
from . import utils


def scan() -> Exporter:
    targets = utils.objects_selected_or_roots()
    scanner = Exporter()
    scanner.scan(targets)
    return scanner


def load(collection: bpy.types.Collection,
         roots: List[pyscene.Node],
         vrm: Optional[pyscene.Vrm] = None):
    importer = Importer(collection, vrm)
    importer.execute(roots)
