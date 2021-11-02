from typing import List, Optional, Tuple, Union, NamedTuple
from .mesh import Mesh, ExportMesh
from .humanoid import HumanoidBones


class RotationConstraint(NamedTuple):
    target: 'Node'
    weight: float


class Skin:
    def __init__(self):
        self.joints: List[Node] = []


class Node:
    def __init__(self, name: str):
        self.name = name
        self.children: List[Node] = []
        self.parent: Optional[Node] = None
        self.translation: Tuple[float, float, float] = (0, 0, 0)
        self.rotation: Tuple[float, float, float, float] = (0, 0, 0, 1)
        self.scale: Tuple[float, float, float] = (1, 1, 1)
        self.mesh: Union[Mesh, ExportMesh, None] = None
        self.skin: Optional[Skin] = None
        self.humanoid_bone: Optional[HumanoidBones] = None
        self.constraint: Union[RotationConstraint, None] = None

    def add_child(self, child: 'Node'):
        child.parent = self
        self.children.append(child)

    def traverse(self):
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x
