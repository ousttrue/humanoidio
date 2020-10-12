import scene_translator
import bpy

print('register')
scene_translator.register()

print('call')
bpy.ops.object.cursor_array()

print('unregister')
scene_translator.unregister()
