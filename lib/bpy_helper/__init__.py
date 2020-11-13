from typing import Collection, List, Optional
from contextlib import contextmanager
import bpy, mathutils
from .. import pyscene
from .. import formats
from .exporter import Exporter
from .importer import Importer
from .functions import remove_mesh


def objects_selected_or_roots(
        selected_only: bool = False) -> List[bpy.types.Object]:
    if selected_only:
        return [o for o in bpy.context.selected_objects]
    else:
        return [o for o in bpy.data.scenes[0].objects if not o.parent]


mode_map = {
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
def disposable_mode(mode='OBJECT'):
    restore = mode_map[bpy.context.mode]
    try:
        if restore != mode:
            bpy.ops.object.mode_set(mode=mode, toggle=False)
        yield None
    finally:
        if bpy.context.mode != restore:
            bpy.ops.object.mode_set(mode=restore, toggle=False)


# @contextmanager
# def tmp_mode(obj, tmp: str):
#     mode = obj.rotation_mode
#     obj.rotation_mode = tmp
#     try:
#         yield
#     finally:
#         obj.rotation_mode = mode


def enter_mode(mode='OBJECT'):
    restore = mode_map[bpy.context.mode]  # EDIT_ARMATURE
    if restore != mode:
        bpy.ops.object.mode_set(mode=mode, toggle=False)


@contextmanager
def disposable(obj: bpy.types.Object):
    try:
        yield None
    finally:
        remove_mesh(obj)


def apply_transform(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)
    obj.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')


def clone(obj: bpy.types.Object) -> bpy.types.Object:
    enter_mode('OBJECT')

    new_obj: bpy.types.Object = obj.copy()
    new_obj.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(new_obj)

    return new_obj


def clone_and_apply_transform(obj: bpy.types.Object) -> bpy.types.Object:
    new_obj = clone(obj)

    # apply transform
    if obj.parent:
        location, rotation, scale = obj.matrix_world.decompose()
        new_obj.location = location
        new_obj.rotation_quaternion = rotation
        new_obj.scale = scale
        layer = bpy.context.view_layer
        layer.update()
    apply_transform(new_obj)

    # TODO: 近接頂点の統合

    return new_obj


def apply_shape_key(obj: bpy.types.Object, i: int):
    bl_mesh: bpy.types.Mesh = obj.data
    for shape in bl_mesh.shape_keys.key_blocks:
        print(shape)


def remove_shapekey_except(obj: bpy.types.Object, i: int):
    shape_keys = len(obj.data.shape_keys.key_blocks)
    for j in reversed(range(0, shape_keys)):
        if j == i:
            continue
        obj.active_shape_key_index = j
        bpy.ops.object.shape_key_remove()


def apply_modifiers(obj: bpy.types.Object):
    '''
    Armatureまで適用する
    '''
    bpy.context.view_layer.objects.active = obj
    enter_mode('OBJECT')
    modifiers = []
    for m in obj.modifiers:
        modifiers.append(m.name)
        if m.type == 'ARMATURE':
            break

    for m in modifiers:
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m)


def scan() -> Exporter:
    targets = objects_selected_or_roots()
    scanner = Exporter()
    scanner.scan(targets)
    return scanner


def load(collection: bpy.types.Collection,
         roots: List[pyscene.Node],
         vrm: Optional[pyscene.Vrm] = None):
    importer = Importer(collection, vrm)
    importer.execute(roots)


def clear():
    # clear scene
    bpy.ops.object.select_all(action='SELECT')  # type: ignore
    bpy.ops.object.delete()

    # only worry about data in the startup scene
    for bpy_data_iter in (
            bpy.data.objects,
            bpy.data.meshes,
            bpy.data.lights,
            bpy.data.cameras,
            bpy.data.materials,
    ):
        for id_data in bpy_data_iter:
            # id_data.user_clear();
            bpy_data_iter.remove(id_data)
