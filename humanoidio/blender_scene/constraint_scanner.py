from typing import List
import bpy
from .types import bl_obj_gltf_node
from .. import gltf


def find(obj_node: List[bl_obj_gltf_node], target: bpy.types.Object):
    for bl_obj, node in obj_node:
        if bl_obj == target:
            return node


def scan(obj_node: List[bl_obj_gltf_node]):
    '''
    https://docs.blender.org/api/current/bpy.types.CopyRotationConstraint.html
    '''
    for bl_obj, node in obj_node:
        for c in bl_obj.constraints:
            if isinstance(c, bpy.types.CopyRotationConstraint):
                src = find(obj_node, c.target)
                if src:
                    node.constraint = gltf.RotationConstraint(src, c.influence)
