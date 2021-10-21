from logging import getLogger

logger = getLogger(__name__)

import bpy
from bpy_extras.io_utils import ExportHelper


class Exporter(bpy.types.Operator, ExportHelper):
    bl_idname = 'humanoidio.exporter'
    bl_label = 'humanoidio Exporter'
    bl_options = {'PRESET'}

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')

        logger.debug('#### end ####')
        return {'FINISHED'}
