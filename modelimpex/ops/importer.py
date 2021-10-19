import bpy
from bpy_extras.io_utils import ImportHelper
from logging import getLogger
import pathlib
from .. import gltf

logger = getLogger(__name__)


class Importer(bpy.types.Operator, ImportHelper):
    bl_idname = "modelimpex.importer"
    bl_label = "Model Importer"

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')
        # read file
        loader = gltf.load(pathlib.Path(self.filepath).absolute())
        # build mesh

        logger.debug('#### end ####')
        return {'FINISHED'}
