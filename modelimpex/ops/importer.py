import bpy
from bpy_extras.io_utils import ImportHelper
from logging import getLogger

logger = getLogger(__name__)


class Importer(bpy.types.Operator, ImportHelper):
    bl_idname = "modelimpex.importer"
    bl_label = "Model Importer"

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')
        return {'FINISHED'}
