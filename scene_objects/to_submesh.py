from typing import List
import array
from scene_translator.formats.buffertypes import Vector2, Vector3, IVector4, Vector4
from .facemesh import FaceMesh
from .submesh_mesh import SubmeshMesh


def facemesh_to_submesh(self: FaceMesh,
                        skin_bone_names: List[str]) -> SubmeshMesh:
    '''
    blenderの面毎にmaterialを持つ形式から、
    同じmaterialをsubmeshにまとめた形式に変換する
    '''

    # 三角形をsubmeshに分配する
    dst = SubmeshMesh(self.name)
    for triangle in self.triangles:
        submesh = dst.get_or_create_submesh(triangle.material_index,
                                            self.materials)
        submesh.indices += array.array('I',
                                       (triangle.i0, triangle.i1, triangle.i2))

    keys = sorted(dst.submesh_map.keys())
    total_vertex_count = 0
    for key in keys:
        submesh = dst.submesh_map[key]
        total_vertex_count += len(submesh.indices)
    dst.vertex_count = total_vertex_count

    # attributes
    positions = (Vector3 * total_vertex_count)()
    normals = (Vector3 * total_vertex_count)()
    uvs = (Vector2 * total_vertex_count)() if any(
        f.uv for f in self.face_vertices) else None
    joints = (IVector4 * total_vertex_count)()
    weights = (Vector4 * total_vertex_count)()
    has_bone_weights = skin_bone_names and len(skin_bone_names) > 0
    if has_bone_weights:
        group_index_to_joint_index = {
            i: skin_bone_names.index(vertex_group)
            for i, vertex_group in enumerate(self.vertex_group_names)
            if vertex_group in skin_bone_names
        }

    morph_map = {}
    for k, morph in self.morph_map.items():
        morph_positions = (Vector3 * total_vertex_count)()
        morph_map[k] = morph_positions

    # each submesh
    i = 0
    for key in keys:
        submesh = dst.submesh_map[key]

        for index in submesh.indices:
            face = self.face_vertices[index]
            positions[i] = self.positions[face.position_index]
            if face.normal:
                normals[i] = face.normal
            else:
                normals[i] = self.normals[face.position_index]
            uvs[i] = face.uv

            if has_bone_weights:
                bone_weight = self.bone_weights[face.position_index]
                joints[i], weights[i] = bone_weight.to_joints_with_weights(
                    group_index_to_joint_index)

            for k, morph in self.morph_map.items():
                morph_positions = morph_map[k]
                morph_positions[i] = morph[face.position_index]
            i += 1

    # sort
    dst.submeshes = [dst.submesh_map[key] for key in keys]
    dst.positions = memoryview(positions)
    dst.normals = memoryview(normals)
    dst.texcoord = memoryview(uvs) if uvs else None
    dst.joints = memoryview(joints) if has_bone_weights else None
    dst.weights = memoryview(weights) if has_bone_weights else None
    dst.morph_map = {k: memoryview(v) for k, v in morph_map.items()}

    return dst
