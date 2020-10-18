from lib.yup.submesh_mesh import SubmeshMesh
from typing import List, Optional, Iterator, Iterable, Union
import bpy, mathutils
from mathutils import Quaternion
from .facemesh import FaceMesh
from ..formats.buffertypes import Vector3, Vector4
from ..formats.vrm0x import HumanoidBones


class Node:
    '''
    GLTF変換との中間形式
    '''
    def __init__(self, name: str, position: mathutils.Vector = None) -> None:
        self.name = name
        if position:
            self.position = Vector3.from_Vector(position)
        else:
            self.position = Vector3(0, 0, 0)
        self.rotation = Vector4(0, 0, 0, 1)
        self.scale = Vector3(1, 1, 1)
        self.parent: Optional[Node] = None
        self.children: List[Node] = []
        self.mesh: Union[SubmeshMesh, FaceMesh, None] = None
        self.skin: Optional[Node] = None
        self.humanoid_bone: Optional[HumanoidBones] = None

        # self.gltf_node = gltf_node
        # self.blender_object: bpy.types.Object = None
        # self.blender_armature: bpy.types.Object = None
        # self.blender_bone: bpy.types.Bone = None
        # self.bone_name: str = ''

        # self.name = self.gltf_node.name
        # if not self.name:
        #     self.name = '_%03d' % self.index

    def get_root(self):
        current = self
        while True:
            if not current.parent:
                return current
            current = current.parent

    def add_child(self, child: 'Node'):
        for node in self.get_root().traverse():
            if node == child:
                raise Exception("recursive")

        if child.parent:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: 'Node'):
        if child not in self.children:
            return
        self.children.remove(child)
        child.parent = None

    def __repr__(self) -> str:
        return f'[{self.name} {self.position}]'

    def __str__(self) -> str:
        return f'<Node {self.name}>'

    def traverse(self) -> Iterator['Node']:
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x

    def get_local_position(self) -> Vector3:
        if self.parent:
            return self.position - self.parent.position
        else:
            return self.position


# class _Node:
#     def __str__(self) -> str:
#         return f'{self.index}'

#     def __repr__(self) -> str:
#         return f'<{self.index}: {self.blender_object}>'

#     def traverse(self) -> Iterable['Node']:
#         yield self
#         for child in self.children:
#             for x in child.traverse():
#                 yield x

#     def get_ancestors(self) -> Iterable['Node']:
#         yield self
#         if self.parent:
#             for x in self.parent.get_ancestors():
#                 yield x
