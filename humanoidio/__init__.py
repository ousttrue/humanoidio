# This is dummy for development. Main is `../__init__.py`
bl_info = {
    "name": "humanoidio",
    "blender": (2, 93, 0),
    "category": "Import-Export",
}

import bpy
from .ops.importer import Importer, menu as import_menu
from .ops.exporter import Exporter, menu as export_menu

CLASSES = [Importer, Exporter]


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_import.append(import_menu)  # type: ignore
    bpy.types.TOPBAR_MT_file_export.append(export_menu)  # type: ignore


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_import.remove(import_menu)  # type: ignore
    bpy.types.TOPBAR_MT_file_export.remove(export_menu)  # type: ignore
