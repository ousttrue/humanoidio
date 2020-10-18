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

from logging import getLogger  # pylint: disable=C0411
logger = getLogger(__name__)
import os
import json
import pathlib
from scene_objects import import_manager
#
import bpy
from .formats import glb, parse_gltf
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (ImportHelper, ExportHelper)


class SceneTranslatorImporter(bpy.types.Operator, ImportHelper):
    """
    Import scene
    """
    bl_idname = 'scene_translator.importer'
    bl_label = 'Scene Importer'
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob: StringProperty(
        default='*.vrm;*.glb;*.gltf',
        options={'HIDDEN'},
    )

    def execute(self, context):
        path = pathlib.Path(self.filepath).absolute()
        gltf, bin = parse_gltf(path)

        from .scene_objects.import_manager import ImportManager
        # return importer.builder.load(context, path, gltf, bin)

        manager = ImportManager(path, gltf, bin)
        manager.load_textures()
        manager.load_materials()
        manager.load_meshes()
        for m, _ in manager.meshes:
            logger.debug(f'[{m.name}: {len(m.vertices)}]vertices')
        nodes, root = manager.load_objects(context)

        # # skinning
        # armature_object = next(node for node in root.traverse()
        #                         if node.blender_armature)

        # for node in nodes:
        #     if node.gltf_node.mesh != -1 and node.gltf_node.skin != -1:
        #         _, attributes = manager.meshes[node.gltf_node.mesh]

        #         skin = gltf.skins[node.gltf_node.skin]
        #         bone_names = [nodes[joint].bone_name for joint in skin.joints]

        #         #armature_object =nodes[skin.skeleton].blender_armature

        #         _setup_skinning(node.blender_object, attributes, bone_names,
        #                         armature_object.blender_armature)

        # remove empties
        _remove_empty(root)

        # done
        # context.scene.update()


class SceneTranslatorExporter(bpy.types.Operator, ExportHelper):
    """
    Export scene
    """
    bl_idname = 'scene_translator.exporter'
    bl_label = 'Scene Exporter'
    bl_options = {'PRESET'}

    filename_ext = '.glb'
    filter_glob: StringProperty(
        default='*.glb',
        options={'HIDDEN'},
    )

    check_extension = True

    def execute(self, context: bpy.types.Context):
        from . import bpy_helper
        targets = bpy_helper.objects_selected_or_roots()

        from . import scene_objects
        scanner = scene_objects.scene_scanner.Scanner()
        scanner.scan(targets)
        scanner.add_mesh_node()
        while True:
            if not scanner.remove_empty_leaf_nodes():
                break

        from . import scanner_to_gltf
        # ext = filepath.suffix
        # is_gltf = (ext == '.gltf')
        data, buffers = scanner_to_gltf.export(scanner)
        d = data.to_dict()

        text = json.dumps(d)
        json_bytes = text.encode('utf-8')
        with open(self.filepath, 'wb') as w:
            glb.Glb(json_bytes, buffers[0].buffer.data).write_to(w)

        return {'FINISHED'}


CLASSES = [SceneTranslatorImporter, SceneTranslatorExporter]


def menu_func_import(self, context):
    self.layout.operator(SceneTranslatorImporter.bl_idname,
                         text=f"Scene Translator (.gltf;.glb;.vrm)")


def menu_func_export(self, context):
    self.layout.operator(SceneTranslatorExporter.bl_idname,
                         text=f"Scene Translator (.glb)")


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for c in CLASSES:
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
