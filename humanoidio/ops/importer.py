from logging import getLogger

logger = getLogger(__name__)

import bpy
from bpy_extras.io_utils import ImportHelper
import pathlib
from .. import gltf
from .. import blender_scene


class Importer(bpy.types.Operator, ImportHelper):
    bl_idname = "humanoidio.importer"
    bl_label = "Model Importer"

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')
        # read file
        path = pathlib.Path(self.filepath).absolute()
        loader = gltf.load(path, gltf.Coodinate.BLENDER_ROTATE)
        # build mesh
        bl_importer = blender_scene.Importer(context)
        bl_importer.load(loader)
        logger.debug('#### end ####')
        return {'FINISHED'}
