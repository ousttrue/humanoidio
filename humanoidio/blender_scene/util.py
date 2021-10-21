from contextlib import contextmanager
import bpy

MODE_MAP = {
    'OBJECT': 'OBJECT',
    'EDIT': 'EDIT',
    'EDIT_MESH': 'EDIT',
    'EDIT_ARMATURE': 'EDIT',
    'SCULPT': 'OBJECT',
    'POSE': 'POSE',
    'VERTEX_PAINT': 'OBJECT',
    'WEIGHT_PAINT': 'OBJECT',
    'PAINT_WEIGHT': 'OBJECT',
    'TEXTURE_PAINT': 'OBJECT',
}


@contextmanager
def disposable_mode(bl_obj: bpy.types.Object, mode='OBJECT'):
    '''
    モードを変更して元のモードに戻る
    '''
    bpy.context.view_layer.objects.active = bl_obj
    bl_obj.select_set(True)

    restore = MODE_MAP[bpy.context.mode]
    try:
        if restore != mode:
            bpy.ops.object.mode_set(mode=mode, toggle=False)
        yield None
    finally:
        if bpy.context.mode != restore:
            bpy.ops.object.mode_set(mode=restore, toggle=False)
        bl_obj.select_set(False)
