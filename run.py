from lib import bpy_helper
from logging import getLogger
logger = getLogger(__name__)

from logging import basicConfig, DEBUG
basicConfig(
    level=DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

import os
import bpy
import pyimpex
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
os.chdir(HERE)
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore
VRM_SAMPLE_DIR = pathlib.Path(os.getenv('VRM_SAMPLES'))  # type: ignore
# SRC_FILE = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
# SRC_FILE = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF/BoxTextured.gltf'
# SRC_FILE = GLTF_SAMPLE_DIR / '2.0/RiggedSimple/glTF/RiggedSimple.gltf'
# SRC_FILE = GLTF_SAMPLE_DIR / '2.0/AlphaBlendModeTest/glTF/AlphaBlendModeTest.gltf'
# SRC_FILE = GLTF_SAMPLE_DIR / '2.0/DamagedHelmet/glTF/DamagedHelmet.gltf'
# SRC_FILE = GLTF_SAMPLE_DIR / '2.0/AnimatedMorphCube/glTF/AnimatedMorphCube.gltf'
# SRC_FILE = GLTF_SAMPLE_DIR / '2.0/UnlitTest/glTF/UnlitTest.gltf'
SRC_FILE = VRM_SAMPLE_DIR / 'vroid/Vivi.vrm'
pyimpex.register()
DST_FILE = HERE / 'tmp.glb'

# clear scene
logger.debug('clear scene')
bpy_helper.clear()

bpy.ops.pyimpex.importer(filepath=str(SRC_FILE))  # type: ignore
bpy.ops.pyimpex.exporter(filepath=str(DST_FILE))  # type: ignore

# TODO: validate

# cleanup
pyimpex.unregister()
