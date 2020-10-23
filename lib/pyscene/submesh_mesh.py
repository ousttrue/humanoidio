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


class MorphTarget:
    def __init__(self, name):
        self.name = name


class SubmeshMesh:
    def __init__(self, name: str, vertex_count: int, has_bone_weight: bool):
        self.name = name
        self.attributes = PlanarBuffer.create(vertex_count, has_bone_weight)
        # morph
        self.morph_map: Dict[str, memoryview] = {}
        # indices
        self.indices = array.array('I')
        self.submeshes: List[Submesh] = []
        # morph targets
        self.morphtargets: List[MorphTarget] = []

    def __str__(self) -> str:
        vertex_count = self.attributes.get_vertex_count()
        submeshes = [
            f'[{sm.material.__class__.__name__}]' for sm in self.submeshes
        ]
        return f'<SubmeshMesh: {vertex_count}verts {"".join(submeshes)}>'
