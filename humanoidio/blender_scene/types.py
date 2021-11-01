from typing import NamedTuple
from .. import gltf
import bpy


class bl_obj_gltf_node(NamedTuple):
    bl_obj: bpy.types.Object
    node: gltf.Node
