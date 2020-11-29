from typing import List, Optional
import bpy, mathutils
from .. import pyscene
from . import utils, importer, exporter


def reload():
    print(f'reload {__file__}')
    from . import exporter, importer, utils
    import importlib
    for m in [exporter, importer, utils]:
        importlib.reload(m)


def scan() -> exporter.Exporter:
    targets = utils.objects_selected_or_roots()
    scanner = exporter.Exporter()
    scanner.scan(targets)
    return scanner


def load(collection: bpy.types.Collection,
         roots: List[pyscene.Node],
         vrm: Optional[pyscene.Vrm] = None):
    imp = importer.Importer(collection, vrm)
    imp.execute(roots)
