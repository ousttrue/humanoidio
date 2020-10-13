import scene_translator
import bpy

print('register')
scene_translator.register()

print('## import ##')
bpy.ops.scene_translator.importer(filepath='tmp.glb')
print()
print('## export ##')
bpy.ops.scene_translator.exporter(filepath='tmp.glb')
print()

print('unregister')
scene_translator.unregister()
