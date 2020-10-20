from logging import getLogger
logger = getLogger(__name__)

from logging import basicConfig, DEBUG
basicConfig(
    level=DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

import os
import bpy
import scene_translator
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
os.chdir(HERE)
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore
SRC_FILE = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
scene_translator.register()
DST_FILE = HERE / 'tmp.glb'

# clear scene
logger.debug('clear scene')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.scene_translator.importer(filepath=str(SRC_FILE))  # type: ignore
bpy.ops.scene_translator.exporter(filepath=str(DST_FILE))  # type: ignore

# cleanup
scene_translator.unregister()
