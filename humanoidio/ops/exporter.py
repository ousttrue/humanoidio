from logging import getLogger

logger = getLogger(__name__)

import bpy
from bpy_extras.io_utils import ExportHelper

from .. import blender_scene
import pathlib


class Exporter(bpy.types.Operator, ExportHelper):
    bl_idname = 'humanoidio.exporter'
    bl_label = 'humanoidio Exporter'
    bl_options = {'PRESET'}

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')

        # scan scene
        objs = bpy.context.selected_objects
        if not objs:
            objs = bpy.context.collection.objects
        exporter = blender_scene.exporter.export(objs)

        # serialize
        glb = exporter.to_glb()
        path = pathlib.Path(self.filepath)

        logger.debug(f'write {len(glb)} bytes to {path}')
        path.write_bytes(glb)

        return {'FINISHED'}
