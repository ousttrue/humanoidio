# This is dummy for development. Main is `../__init__.py`
bl_info = {
    "name": "modelimpex",
    "blender": (2, 93, 0),
    "category": "Import-Export",
}

import bpy
from .ops.importer import Importer

CLASSES = [Importer]


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
