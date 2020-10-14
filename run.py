import os
import bpy
import scene_translator

print('register')
scene_translator.register()

GLB_FILE = 'tmp.glb'

print('## export ##')
bpy.ops.scene_translator.exporter(filepath=GLB_FILE)
print()

print('## import ##')
bpy.ops.scene_translator.importer(filepath=GLB_FILE)
print()

os.remove(GLB_FILE)

print('unregister')
scene_translator.unregister()
