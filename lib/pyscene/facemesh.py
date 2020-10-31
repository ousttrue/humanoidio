from logging import getLogger
logger = getLogger(__name__)
from typing import (Any, List, Dict, Optional, NamedTuple, Sequence, MutableSequence)
import bpy, mathutils
from ..struct_types import Float2, Float3, BoneWeight
from .material import UnlitMaterial


class FaceVertex(NamedTuple):
    material_index: int
    position_index: int
    normal: Float3
    uv: Optional[Float2]

    def __hash__(self):
        return hash(self.position_index)

    def __eq__(self, other: 'FaceVertex') -> bool:
        if other is None or not isinstance(other, FaceVertex):
            return False
        if self.material_index != other.material_index:
            return False
        if self.position_index != other.position_index:
            return False
        if self.normal != other.normal:
            return False
        if self.uv != other.uv:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class Triangle(NamedTuple):
    material_index: int
    i0: int
    i1: int
    i2: int
    normal: Optional[Float3]


class FaceMesh:
    def __init__(self, name: str, vertices: List[bpy.types.MeshVertex],
                 materials: List[UnlitMaterial],
                 vertex_groups: List[bpy.types.VertexGroup],
                 bone_names: List[str]) -> None:
        self.name = name
        self.positions: Any = (Float3 * len(vertices))()
        self.normals: Any = (Float3 * len(vertices))()
        for i, v in enumerate(vertices):
            self.positions[i] = Float3(v.co.x, v.co.y, v.co.z)
            self.normals[i] = Float3(v.normal.x, v.normal.y, v.normal.z)
        self.materials = materials

        # faces
        self.face_vertices: List[FaceVertex] = []
        self.face_vertex_index_map: Dict[FaceVertex, int] = {}
        self.triangles: List[Triangle] = []

        self.vertex_group_names = [g.name for g in vertex_groups]
        self.bone_names = bone_names
        self.bone_weights = (BoneWeight * len(vertices))()
        for i, v in enumerate(vertices):
            for ve in v.groups:
                vg_name = self.vertex_group_names[ve.group]
                if vg_name in self.bone_names:
                    self.bone_weights[i].push(ve.group, ve.weight)

        self.morph_targets: List[Sequence[Float3]] = []
        self.morph_map: Dict[str, Any] = {}

    def is_face_splitted(self) -> bool:
        return len(self.positions) == len(self.face_vertices)

    def __str__(self) -> str:
        return f'<FaceMesh: {self.name}: {len(self.face_vertices)}vertices>'

    def add_triangle(self, face: bpy.types.MeshLoopTriangle,
                     uv_texture_layer: Optional[bpy.types.MeshUVLoopLayer]):
        def get_uv(i: int) -> Optional[mathutils.Vector]:
            if not uv_texture_layer: return None
            return uv_texture_layer.data[i].uv

        face_normal = None if face.use_smooth else Float3(
            face.normal.x, -face.normal.z, face.normal.y)

        assert len(face.vertices) == 3
        i0 = self._get_or_add_face_vertex(face.material_index,
                                          face.vertices[0],
                                          get_uv(face.loops[0]), face_normal)

        i1 = self._get_or_add_face_vertex(face.material_index,
                                          face.vertices[1],
                                          get_uv(face.loops[1]), face_normal)

        i2 = self._get_or_add_face_vertex(face.material_index,
                                          face.vertices[2],
                                          get_uv(face.loops[2]), face_normal)

        self.triangles.append(
            Triangle(face.material_index, i0, i1, i2, face_normal))

    def _get_or_add_face_vertex(self, material_index: int, vertex_index: int,
                                uv: Optional[mathutils.Vector],
                                face_normal: Optional[Float3]) -> int:
        # 同一頂点を考慮する
        face = FaceVertex(
            material_index, vertex_index,
            face_normal if face_normal else self.normals[vertex_index],
            Float2(uv.x, 1.0 - uv.y) if uv else None)
        index = self.face_vertex_index_map.get(face, None)
        if index != None:
            return index

        index = len(self.face_vertices)
        self.face_vertices.append(face)
        self.face_vertex_index_map[face] = index
        return index

    def add_morph(self, name: str, shape_positions: MutableSequence[Float3]):
        logger.debug(f'add_morph: {name}')
        assert (len(shape_positions) == len(self.positions))
        self.morph_targets.append(shape_positions)  # type: ignore
        self.morph_map[name] = shape_positions
