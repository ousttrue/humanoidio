from logging import getLogger

logger = getLogger(__name__)

import bpy
from bpy_extras.io_utils import ExportHelper

from .. import blender_scene
from .. import gltf
import pathlib


class Exporter(bpy.types.Operator, ExportHelper):
    bl_idname = 'humanoidio.exporter'
    bl_label = 'humanoidio Exporter'
    bl_options = {'PRESET'}

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')

        # scan scene
        bl_obj_list = bpy.context.selected_objects
        if not bl_obj_list:
            # export all
            bl_obj_list = bpy.context.collection.objects
        obj_node = blender_scene.BlenderObjectScanner().scan(bl_obj_list)
        animations = blender_scene.BlenderAnimationScanner().scan(obj_node)

        # serialize
        writer = gltf.exporter.GltfWriter()
        writer.push_scene([node for _, node in obj_node if not node.parent])
        for a in animations:
            writer.push_animation(a, bpy.context.scene.render.fps)
        glb = writer.to_glb()
        path = pathlib.Path(self.filepath)

        logger.debug(f'write {len(glb)} bytes to {path}')
        path.write_bytes(glb)

        return {'FINISHED'}
