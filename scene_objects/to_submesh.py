from typing import List, Dict, NamedTuple
import bpy
from scene_translator.formats.buffertypes import Vector2, Vector3, IVector4, Vector4
from .facemesh import FaceMesh, FaceVertex
from .submesh_mesh import Submesh, SubmeshMesh


class TmpVertex(NamedTuple):
    position: Vector3
    normal: Vector3
    uv: Vector2


class TmpSubmesh:
    def __init__(self, material_index):
        self.material_index = material_index
        self.indices: List[int] = []


class TmpModel:
    def __init__(self):
        self.submeshes: List[TmpSubmesh] = []
        self.submesh_map: Dict[int, TmpSubmesh] = {}
        self.vertices: List[TmpVertex] = []

    def attributes(self):
        positions = (Vector3 * len(self.vertices))()
        normals = (Vector3 * len(self.vertices))()
        uvs = (Vector2 * len(self.vertices))()
        for i, v in enumerate(self.vertices):
            positions[i] = v.position
            normals[i] = v.normal
            uvs[i] = v.uv
        return positions, normals, uvs

    def _get_or_create_submesh(self, material_index: int) -> TmpSubmesh:
        tmp = self.submesh_map.get(material_index)
        if tmp:
            return tmp

        tmp = TmpSubmesh(material_index)
        self.submeshes.append(tmp)
        self.submesh_map[material_index] = tmp
        return tmp

    def _add_vertex(self, position: Vector3, normal: Vector3,
                    uv: Vector2) -> int:
        i = len(self.vertices)
        self.vertices.append(TmpVertex(position, normal, uv))
        return i

    def push_triangle(self, material_index: int, p0: Vector3, p1: Vector3,
                      p2: Vector3, n0: Vector3, n1: Vector3, n2: Vector3, uv0,
                      uv1, uv2):
        submesh = self._get_or_create_submesh(material_index)
        submesh.indices.append(self._add_vertex(p0, n0, uv0))
        submesh.indices.append(self._add_vertex(p1, n1, uv1))
        submesh.indices.append(self._add_vertex(p2, n2, uv2))


def facemesh_to_submesh(src: FaceMesh,
                        skin_bone_names: List[str]) -> SubmeshMesh:
    '''
    blenderの面毎にmaterialを持つ形式から、
    同じmaterialをsubmeshにまとめた形式に変換する
    '''

    # 三角形をsubmeshに分配する
    tmp = TmpModel()
    for t in src.triangles:
        fv0 = src.face_vertices[t.i0]
        fv1 = src.face_vertices[t.i1]
        fv2 = src.face_vertices[t.i2]

        p0 = src.positions[fv0.position_index]
        p1 = src.positions[fv1.position_index]
        p2 = src.positions[fv2.position_index]

        if t.normal:
            n0 = n1 = n2 = t.normal
        else:
            n0 = src.normals[fv0.normal_index]
            n1 = src.normals[fv1.normal_index]
            n2 = src.normals[fv2.normal_index]

        uv0 = fv0.uv if fv0.uv else Vector2(0, 0)
        uv1 = fv1.uv if fv1.uv else Vector2(0, 0)
        uv2 = fv2.uv if fv2.uv else Vector2(0, 0)

        tmp.push_triangle(t.material_index, p0, p1, p2, n0, n1, n2, uv0, uv1,
                          uv2)

    # # each submesh
    # i = 0
    # for key in keys:
    #     submesh = dst.submesh_map[key]

    #     for index in submesh.indices:
    #         face = src.face_vertices[index]

    #         if has_bone_weights:
    #             bone_weight = src.bone_weights[face.position_index]
    #             joints[i], weights[i] = bone_weight.to_joints_with_weights(
    #                 group_index_to_joint_index)

    #         for k, morph in src.morph_map.items():
    #             morph_positions = morph_map[k]
    #             morph_positions[i] = morph[face.position_index]
    #         i += 1

    # attributes
    # total_vertex_count = len(tmp.vertices)
    # joints = (IVector4 * total_vertex_count)()
    # weights = (Vector4 * total_vertex_count)()
    # has_bone_weights = skin_bone_names and len(skin_bone_names) > 0
    # if has_bone_weights:
    #     group_index_to_joint_index = {
    #         i: skin_bone_names.index(vertex_group)
    #         for i, vertex_group in enumerate(src.vertex_group_names)
    #         if vertex_group in skin_bone_names
    #     }

    positions, normals, uvs = tmp.attributes()
    dst = SubmeshMesh(src.name, memoryview(positions))
    dst.normals = memoryview(normals)
    dst.texcoord = memoryview(uvs)
    # dst.joints = memoryview(joints) if has_bone_weights else None
    # dst.weights = memoryview(weights) if has_bone_weights else None
    # morph
    morph_map = {}
    for k, morph in src.morph_map.items():
        morph_positions = (Vector3 * len(tmp.vertices))()
        morph_map[k] = morph_positions
    dst.morph_map = {k: memoryview(v) for k, v in morph_map.items()}
    # submesh
    keys = sorted(tmp.submesh_map.keys())
    for key in keys:
        s = tmp.submesh_map[key]
        if s.material_index < len(src.materials):
            material = src.materials[s.material_index]
        else:
            # default material
            material = bpy.data.materials[0]
        submesh = Submesh(material)
        submesh.indices.extend(s.indices)
        dst.submeshes.append(submesh)

    return dst
