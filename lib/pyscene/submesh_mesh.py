from typing import Any, List, Optional, Dict, Sequence
import array
from ..struct_types import PlanarBuffer
from .material import Material


class Submesh:
    def __init__(self, offset: int, vertex_count: int,
                 material: Material) -> None:
        self.material = material
        self.offset = offset
        self.vertex_count = vertex_count

    def compare(self, other) -> bool:
        if not isinstance(other, Submesh):
            raise Exception('other is not Submesh')
        if not self.material.compare(other.material):
            raise Exception('self.material != other.material')
        if self.offset != other.offset:
            raise Exception('self.offset != other.offset')
        if self.vertex_count != other.vertex_count:
            raise Exception('self.vertex_count != other.vertex_count')
        return True


class MorphTarget:
    def __init__(self, name: str, vertex_count: int):
        self.name = name
        self.attributes = PlanarBuffer.create(vertex_count, False)

    def __str__(self):
        return f'<PlanarBuffer {self.attributes.get_vertex_count()}>'


class SubmeshMesh:
    def __init__(self, name: str, vertex_count: int, has_bone_weight: bool):
        self.name = name
        self.attributes = PlanarBuffer.create(vertex_count, has_bone_weight)
        # morph
        # self.morph_map: Dict[str, memoryview] = {}
        # indices
        self.indices = array.array('I')
        self.submeshes: List[Submesh] = []
        # morph targets
        self.morphtargets: List[MorphTarget] = []

    def __repr__(self):
        return str(self)

    def __str__(self) -> str:
        vertex_count = self.attributes.get_vertex_count()
        submeshes = [
            f'[{sm.material.__class__.__name__}]' for sm in self.submeshes
        ]
        morph = f' {len(self.morphtargets)}morph' if self.morphtargets else ''
        return f'<SubmeshMesh: {vertex_count}verts {"".join(submeshes)}{morph}>'

    def compare(self, other) -> bool:
        if not isinstance(other, SubmeshMesh):
            raise Exception('r is not SubmeshMesh')

        if self.name != other.name:
            raise Exception(f'{self.name} != {other.name}')

        if not self.attributes.compare(other.attributes):
            raise Exception(f'{self.attributes} != {other.attributes}')

        if self.indices != other.indices:
            raise Exception(f'{self.indices} != {other.indices}')

        if len(self.morphtargets) != len(other.morphtargets):
            raise Exception(
                'len(self.morphtargets) != len(other.morphtargets)')
        for l, r in zip(self.morphtargets, other.morphtargets):
            if l != r:
                raise Exception(f'{l} != {r}')

        if len(self.submeshes) != len(other.submeshes):
            raise Exception('len(self.submeshes) != len(other.submeshes)')
        for l, r in zip(self.submeshes, other.submeshes):
            if not l.compare(r):
                raise Exception(f'{l} != {r}')

        return True

    def get_or_create_morphtarget(self, i: int) -> MorphTarget:
        if i < len(self.morphtargets):
            return self.morphtargets[i]

        if len(self.morphtargets) != i:
            raise Exception()

        morphtarget = MorphTarget(f'{i}', self.attributes.get_vertex_count())
        self.morphtargets.append(morphtarget)
        return morphtarget
