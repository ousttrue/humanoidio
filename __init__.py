'''
* https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo#Script_Meta_Info
* https://github.com/dfelinto/blender/blob/master/release/scripts/modules/addon_utils.py
'''
bl_info = {
    "name": "scene_translator",
    "author": "ousttrue",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "scene import and export",
    "doc_url": "https://github.com/ousttrue/scene_translator",
    "category": "Import-Export",
    "support": "TESTING",
    "warning": "This addon is still in development.",
}

import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (ExportHelper)


class SceneTranslatorExporter(bpy.types.Operator, ExportHelper):
    """Save a Scene"""

    bl_idname = "scene_translator.exporter"
    bl_label = 'Scene Exporter'
    bl_options = {'PRESET'}

    filename_ext = ".glb"
    filter_glob: StringProperty(
        default="*.glb",
        options={'HIDDEN'},
    )

    check_extension = True

    def execute(self, context: bpy.types.Context):
        import exporter
        exporter.run(context)
        return {'FINISHED'}


def menu_func_export(self, context):
    self.layout.operator(SceneTranslatorExporter.bl_idname,
                         text="Scene Exporter (.glb)")


def register():
    bpy.utils.register_class(SceneTranslatorExporter)
    bpy.types.VIEW3D_MT_object.append(menu_func_export)


def unregister():
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    bpy.utils.unregister_class(SceneTranslatorExporter)
    bpy.types.VIEW3D_MT_object.remove(menu_func_export)


if __name__ == "__main__":
    register()
