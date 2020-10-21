from typing import List, Optional, Iterator, Iterable, Union
import bpy, mathutils
from .submesh_mesh import SubmeshMesh
from .facemesh import FaceMesh
from ..formats.vrm0x import HumanoidBones
from ..struct_types import Float3, Float4


class Skin:
    def __init__(self, name: str, root: 'Node', joints: List['Node']):
        self.name = name
        self.root = root
        self.joints = joints


class Node:
    '''
    GLTF変換との中間形式
    '''
    def __init__(self, name: str, position: mathutils.Vector = None) -> None:
        self.name = name
        if position:
            self.position = Float3.from_Vector(position)
        else:
            self.position = Float3(0, 0, 0)
        self.rotation = Float4(0, 0, 0, 1)
        self.scale = Float3(1, 1, 1)
        self.parent: Optional[Node] = None
        self.children: List[Node] = []
        self.mesh: Union[SubmeshMesh, FaceMesh, None] = None
        self.skin: Optional[Skin] = None
        self.humanoid_bone: Optional[HumanoidBones] = None

        # self.gltf_node = gltf_node
        # self.blender_object: bpy.types.Object = None
        # self.blender_armature: bpy.types.Object = None
        # self.blender_bone: bpy.types.Bone = None
        # self.bone_name: str = ''

        # self.name = self.gltf_node.name
        # if not self.name:
        #     self.name = '_%03d' % self.index

    def __getitem__(self, i: int) -> 'Node':
        return self.children[i]

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
        if not self.mesh:
            return f'<Node {self.name}>'
        return f'<Node {self.name}: {self.mesh}>'

    def traverse(self) -> Iterator['Node']:
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x

    def get_local_position(self) -> Float3:
        if self.parent:
            return self.position - self.parent.position
        else:
            return self.position

    def has_mesh(self) -> bool:
        has_mesh = False

        def check_has_mesh(n: Node):
            if n.mesh:
                has_mesh = True
                return
            for c in n.children:
                check_has_mesh(c)

        check_has_mesh(self)
        return has_mesh
