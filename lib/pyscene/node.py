from typing import List, Optional, Iterator, Union
from .submesh_mesh import SubmeshMesh
from .facemesh import FaceMesh
from ..formats.vrm0x import HumanoidBones
from ..struct_types import Float3, Float4


class Skin:
    def __init__(self, name: str):
        self.name = name
        self.joints: List[Node] = []

    def get_root_joints(self):
        i = 0
        for joint in self.joints:
            is_root = True
            aa = [a for a in joint.get_ancestors()]
            for a in aa:
                if a == joint:
                    continue
                if a in self.joints:
                    is_root = False
                    break
            if is_root:
                yield joint
                i += 1
        if i == 0:
            raise Exception()


# class Skin:
#     def __init__(self, manager: 'ImportManager', skin: gltf.Skin) -> None:
#         self.manager = manager
#         self.skin = skin
#         self.inverse_matrices: Any = None

#     def get_matrix(self, joint: int) -> Any:
#         if not self.inverse_matrices:
#             self.inverse_matrices = self.manager.get_array(
#                 self.skin.inverseBindMatrices)
#         m = self.inverse_matrices[joint]
#         mat = mathutils.Matrix(
#             ((m.f00, m.f10, m.f20, m.f30), (m.f01, m.f11, m.f21, m.f31),
#              (m.f02, m.f12, m.f22, m.f32), (m.f03, m.f13, m.f23, m.f33)))
#         # d = mat.decompose()
#         return mat


class Node:
    '''
    GLTF変換との中間形式
    '''
    def __init__(self, name: str) -> None:
        self.name = name
        self.position = Float3(0, 0, 0)
        self.rotation = Float4(0, 0, 0, 1)
        self.scale = Float3(1, 1, 1)
        self.parent: Optional[Node] = None
        self.children: List[Node] = []
        self.mesh: Union[SubmeshMesh, FaceMesh, None] = None
        self.skin: Optional[Skin] = None
        self.humanoid_bone: Optional[HumanoidBones] = None

    def __getitem__(self, i: int) -> 'Node':
        return self.children[i]

    def __repr__(self) -> str:
        return f'<{self.name} {self.position}>'

    def __str__(self) -> str:
        if not self.mesh:
            return f'<Node {self.name}>'
        return f'<Node {self.name}: {self.mesh}>'

    def get_ancestors(self):
        current = self
        while True:
            yield current
            if not current.parent:
                break
            current = current.parent

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

    def traverse(self) -> Iterator['Node']:
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x

    def contains(self, joints: List['Node']) -> bool:
        descendants = [node for node in self.traverse()][1:]
        for j in joints:
            if j not in descendants:
                return False
        return True

    def get_local_position(self) -> Float3:
        if self.parent:
            return self.position - self.parent.position
        else:
            return self.position

    def has_mesh(self) -> bool:
        has_mesh = []

        def check_has_mesh(n: Node):
            if n.mesh:
                has_mesh.append(True)
                return
            for c in n.children:
                check_has_mesh(c)

        check_has_mesh(self)
        return len(has_mesh) > 0
