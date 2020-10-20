from logging import getLogger
logger = getLogger(__name__)
import json
import pathlib
from typing import Set, List
import bpy
from scene_translator.formats.glb import Glb
from scene_translator.formats.gltf import glTF

from .import_manager import ImportManager

from .material_io import load_materials
from .mesh_io import load_meshes
from .node_io import load_objects
from .node import Node
# from . import gltf_buffer

from logging import getLogger  # pylint: disable=C0411
logger = getLogger(__name__)

# def _setup_skinning(blender_object: bpy.types.Object,
#                     attributes: gltf_buffer.VertexBuffer,
#                     bone_names: List[str],
#                     armature_object: bpy.types.Object) -> None:
#     # create vertex groups
#     for bone_name in bone_names:
#         if bone_name:
#             blender_object.vertex_groups.new(name=bone_name)

#     idx_already_done: Set[int] = set()

#     # each face
#     for poly in blender_object.data.polygons:
#         # face vertex index
#         for loop_idx in range(poly.loop_start,
#                               poly.loop_start + poly.loop_total):
#             loop = blender_object.data.loops[loop_idx]
#             vert_idx = loop.vertex_index
#             if vert_idx < 0:
#                 raise Exception()
#             if vert_idx >= len(attributes.joints):
#                 raise Exception()

#             if vert_idx in idx_already_done:
#                 continue
#             idx_already_done.add(vert_idx)

#             cpt = 0
#             for joint_idx in attributes.joints[vert_idx]:
#                 if cpt > 3:
#                     break
#                 weight_val = attributes.weights[vert_idx][cpt]
#                 if weight_val != 0.0:
#                     # It can be a problem to assign weights of 0
#                     # for bone index 0, if there is always 4 indices in joint_ tuple
#                     bone_name = bone_names[joint_idx]
#                     if bone_name:
#                         group = blender_object.vertex_groups[bone_name]
#                         group.add([vert_idx], weight_val, 'REPLACE')
#                 cpt += 1

#     # select
#     # for obj_sel in bpy.context.scene.objects:
#     #    obj_sel.select = False
#     #blender_object.select = True
#     #bpy.context.scene.objects.active = blender_object

#     modifier = blender_object.modifiers.new(name="Armature", type="ARMATURE")
#     modifier.object = armature_object


def _remove_empty(node: Node):
    for i in range(len(node.children) - 1, -1, -1):
        child = node.children[i]
        _remove_empty(child)

    if node.children:
        return
    if node.blender_armature:
        return
    if node.blender_object.data:
        return

    # remove empty
    bpy.data.objects.remove(node.blender_object, do_unlink=True)
    if node.parent:
        node.parent.children.remove(node)
