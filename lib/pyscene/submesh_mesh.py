from typing import Any, List, NamedTuple, Optional
import array
from ..struct_types import PlanarBuffer, Float2, Float3, Float4, UShort4
from .material import UnlitMaterial


class Submesh:
    def __init__(self, offset: int, vertex_count: int,
                 material: UnlitMaterial) -> None:
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
        return f'{self.name}: <PlanarBuffer {len(self.attributes.position)}>'

    def __repr__(self):
        return str(self)


class Vertex(NamedTuple):
    position: Float3
    normal: Float3
    uv: Float2
    joints: UShort4
    weights: Float4

    @staticmethod
    def zero() -> 'Vertex':
        return Vertex(Float3(), Float3(), Float2(), UShort4(), Float4())


class SubmeshMesh:
    def __init__(self, name: str):
        self.name = name
        self.attributes: Optional[
            PlanarBuffer] = None  # PlanarBuffer.create(vertex_count, has_bone_weight)
        # morph
        # self.morph_map: Dict[str, memoryview] = {}
        # indices
        self.indices = array.array('I')
        self.submeshes: List[Submesh] = []
        # morph targets
        self.morphtargets: List[MorphTarget] = []
        self.vertex_count = 0

    def __repr__(self):
        return str(self)

    def __str__(self) -> str:
        submeshes = [
            f'[{sm.material.__class__.__name__}]' for sm in self.submeshes
        ]
        morph = f' {len(self.morphtargets)}morph' if self.morphtargets else ''
        return f'<SubmeshMesh: {self.vertex_count}verts {"".join(submeshes)}{morph}>'

    def set_vertices(self, vertices: List[Vertex]):
        positions = (Float3 * len(vertices))()
        normals = (Float3 * len(vertices))()
        texcoords = (Float2 * len(vertices))()
        joints = (UShort4 * len(vertices))()
        weights = (Float4 * len(vertices))()
        for i, v in enumerate(vertices):
            positions[i] = v.position
            normals[i] = v.normal
            texcoords[i] = v.uv
            joints[i] = v.joints
            weights[i] = v.weights

        self.attributes = PlanarBuffer(positions, normals, texcoords, joints,
                                       weights)
        self.vertex_count = len(vertices)

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
            if l.name != r.name:
                raise Exception(f'{l.name} != {r.name}')
            if not l.attributes.compare(r.attributes):
                return False

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

        morphtarget = MorphTarget(f'{i}', self.vertex_count)
        self.morphtargets.append(morphtarget)
        return morphtarget

    def create_from_submesh(self, i: int) -> 'SubmeshMesh':
        submesh = self.submeshes[i]
        mesh = SubmeshMesh(f'self.name:{i}')

        index_map = {}
        for i, index_index in enumerate(
                range(submesh.offset, submesh.offset + submesh.vertex_count)):
            vertex_index = self.indices[index_index]
            try:
                dst_index = index_map[vertex_index]
            except KeyError:
                dst_index = len(index_map)
                index_map[vertex_index] = dst_index
                mesh.attributes.copy_vertex_from(dst_index, self.attributes,
                                                 vertex_index)
            mesh.indices.append(dst_index)
        mesh.submeshes.append(
            Submesh(0, submesh.vertex_count, submesh.material))
        mesh.vertex_count = len(index_map)
        return mesh
