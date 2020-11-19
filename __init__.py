'''
* https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo#Script_Meta_Info
* https://github.com/dfelinto/blender/blob/master/release/scripts/modules/addon_utils.py
'''
bl_info = {
    "name": "pyimpex",
    "author": "ousttrue",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "scene import and export",
    "doc_url": "https://github.com/ousttrue/pyimpex",
    "category": "Import-Export",
    "support": "TESTING",
    "warning": "This addon is still in development.",
}

from logging import getLogger
logger = getLogger(__name__)
import json
import pathlib


def reload():
    print('reload')
    import importlib
    from .lib import formats
    importlib.reload(formats)

    from .lib import pyscene
    importlib.reload(pyscene)
    pyscene.reload()


if "bpy" in locals():
    reload()

#
import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (ImportHelper, ExportHelper)


class PyImpexImporter(bpy.types.Operator, ImportHelper):
    """
    Import scene
    """
    bl_idname = 'pyimpex.importer'
    bl_label = 'Scene Importer'
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob: StringProperty(
        default='*.vrm;*.glb;*.gltf',
        options={'HIDDEN'},
    )

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')

        #
        # read data
        #
        path = pathlib.Path(self.filepath).absolute()  # type: ignore

        from .lib import formats
        data = formats.parse_gltf(path)

        from .lib import pyscene
        index_map = pyscene.load(data)
        roots = index_map.get_roots(data.gltf)
        vrm = pyscene.load_vrm(index_map, data.gltf)

        pyscene.modifier.before_import(roots, data.gltf.extensions != None)

        #
        # import to blender
        #
        collection = bpy.data.collections.new(name=path.name)
        context.scene.collection.children.link(collection)

        from .lib import bpy_helper
        bpy_helper.load(collection, roots, vrm)

        # color management
        bpy.context.scene.view_settings.view_transform = 'Standard'

        return {'FINISHED'}


class PyImpexExporter(bpy.types.Operator, ExportHelper):
    """
    Export scene
    """
    bl_idname = 'pyimpex.exporter'
    bl_label = 'Scene Exporter'
    bl_options = {'PRESET'}

    filename_ext = '.glb'
    filter_glob: StringProperty(
        default='*.glb',
        options={'HIDDEN'},
    )

    check_extension = True

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')

        from .lib import bpy_helper
        scanner = bpy_helper.scan()

        from .lib import pyscene
        data = pyscene.to_gltf(scanner.nodes)
        d = data.gltf.to_dict()

        from .lib.formats.glb import Glb
        text = json.dumps(d)
        json_bytes = text.encode('utf-8')
        with open(self.filepath, 'wb') as w:  # type: ignore
            Glb(json_bytes, data.bin).write_to(w)

        return {'FINISHED'}


CLASSES = [PyImpexImporter, PyImpexExporter]


def menu_func_import(self, context):
    self.layout.operator(PyImpexImporter.bl_idname,
                         text=f"pyimpex (.gltf;.glb;.vrm)")


def menu_func_export(self, context):
    self.layout.operator(PyImpexExporter.bl_idname, text=f"pyimpex (.glb)")


def register():
    from .lib.bpy_helper import custom_rna
    custom_rna.register()
    # operators
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)  # type: ignore
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)  # type: ignore


def unregister():
    # Note: when unregister, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for c in CLASSES:
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)  # type: ignore
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)  # type: ignore

    #
    from .lib.bpy_helper import custom_rna
    custom_rna.unregister()


if __name__ == "__main__":
    register()
