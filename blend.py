import sys
import os
import pathlib
import bpy
import pyimpex
from pyimpex.lib import bpy_helper
HERE = pathlib.Path(__file__).absolute().parent
os.chdir(HERE)

print(sys.argv)
path = sys.argv[1]

pyimpex.register()
DST_FILE = HERE / 'tmp/tmp.glb'

bpy.ops.wm.open_mainfile(filepath=path)

bpy.ops.pyimpex.exporter(filepath=str(DST_FILE))  # type: ignore
