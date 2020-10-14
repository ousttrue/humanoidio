import os
import bpy
import scene_translator

print('register')
scene_translator.register()

GLB_FILE = 'tmp.glb'

print(f'## export: {bpy.context.mode} mode')
bpy.ops.scene_translator.exporter(filepath=GLB_FILE)
print(f'{bpy.context.mode} mode')
print()

print(f'## import: {bpy.context.mode} mode')
bpy.ops.scene_translator.importer(filepath=GLB_FILE)
print(f'{bpy.context.mode} mode')
print()

os.remove(GLB_FILE)

print('unregister')
scene_translator.unregister()
