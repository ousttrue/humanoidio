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
GLB_FILE = 'tmp.glb'
# setup
scene_translator.register()

bpy.ops.scene_translator.exporter(filepath=GLB_FILE)
bpy.ops.scene_translator.importer(filepath=GLB_FILE)

# cleanup
os.remove(GLB_FILE)
scene_translator.unregister()
