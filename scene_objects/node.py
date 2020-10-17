from typing import List, Optional, Iterator
import bpy, mathutils
from .facemesh import FaceMesh
from formats.buffertypes import Vector3
from formats.vrm0x import HumanoidBones


class Node:
    def __init__(self, name: str, position: mathutils.Vector = None) -> None:
        self.name = name
        if position:
            self.position = Vector3.from_Vector(position)
        else:
            self.position = Vector3(0, 0, 0)
        self._children: List[Node] = []
        self.parent: Optional[Node] = None
        self.mesh: Optional[FaceMesh] = None
        self.skin: Optional[Node] = None
        self.humanoid_bone: Optional[HumanoidBones] = None

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
        self._children.append(child)

    def remove_child(self, child: 'Node'):
        if child not in self._children:
            return
        self._children.remove(child)
        child.parent = None

    def __repr__(self) -> str:
        return f'[{self.name} {self.position}]'

    def __str__(self) -> str:
        return f'<Node {self.name}>'

    def traverse(self) -> Iterator['Node']:
        yield self
        for child in self._children:
            for x in child.traverse():
                yield x

    def get_local_position(self) -> Vector3:
        if self.parent:
            return self.position - self.parent.position
        else:
            return self.position
