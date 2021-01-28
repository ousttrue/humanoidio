import enum
from typing import List, Dict
from ..struct_types import Float2, Float3
from .node import Node
from .facemesh import FaceMesh
from .submesh_mesh import Submesh, SubmeshMesh


class TmpSubmesh:
    def __init__(self, material_index):
        self.material_index = material_index
        self.indices: List[int] = []


def facemesh_to_submesh(node: Node) -> SubmeshMesh:
    '''
    blenderの面毎にmaterialを持つ形式から、
    同じmaterialをsubmeshにまとめた形式に変換する。
    ついでに、blenderの Z-UP を GLTF のY-UP に変換する
    '''
    if not isinstance(node.mesh, FaceMesh):
        raise Exception()
    src = node.mesh

    submeshes: List[TmpSubmesh] = []
    material_submesh_map: Dict[int, TmpSubmesh] = {}

    def get_or_create_submesh(material_index: int) -> TmpSubmesh:
        tmp = material_submesh_map.get(material_index)
        if tmp:
            return tmp

        tmp = TmpSubmesh(material_index)
        submeshes.append(tmp)
        material_submesh_map[material_index] = tmp
        return tmp

    if src.is_face_splitted():
        positions = [Float3(0, 0, 0)] * len(src.positions)
        normals = [Float3(0, 0, 0)] * len(src.positions)
        texcoords = [Float2(0, 0)] * len(src.positions)
    else:
        positions = []
        normals = []
        texcoords = []

    for t in src.triangles:
        fv0 = src.face_vertices[t.i0]
        fv1 = src.face_vertices[t.i1]
        fv2 = src.face_vertices[t.i2]

        p0 = src.positions[fv0.position_index].zup2yup()
        p1 = src.positions[fv1.position_index].zup2yup()
        p2 = src.positions[fv2.position_index].zup2yup()

        if t.normal:
            n0 = n1 = n2 = t.normal.zup2yup()
        else:
            n0 = fv0.normal.zup2yup()
            n1 = fv1.normal.zup2yup()
            n2 = fv2.normal.zup2yup()

        uv0 = fv0.uv.flip_uv() if fv0.uv else Float2(0, 0)
        uv1 = fv1.uv.flip_uv() if fv1.uv else Float2(0, 0)
        uv2 = fv2.uv.flip_uv() if fv2.uv else Float2(0, 0)

        # TODO: boneweight

        if src.is_face_splitted():
            # Faceが分離済み(positions と face_vertices が一致)
            # 三角形を頂点バッファに展開する
            i0 = fv0.position_index
            i1 = fv1.position_index
            i2 = fv2.position_index
            positions[i0] = p0
            positions[i1] = p1
            positions[i2] = p2
            normals[i0] = n0
            normals[i1] = n1
            normals[i2] = n2
            texcoords[i0] = uv0
            texcoords[i1] = uv1
            texcoords[i2] = uv2
        else:
            i0 = len(positions)
            positions.append(p0)
            i1 = len(positions)
            positions.append(p1)
            i2 = len(positions)
            positions.append(p2)

            normals.append(n0)
            normals.append(n1)
            normals.append(n2)

            texcoords.append(uv0)
            texcoords.append(uv1)
            texcoords.append(uv2)

        submesh = get_or_create_submesh(t.material_index)
        submesh.indices.append(i0)
        submesh.indices.append(i1)
        submesh.indices.append(i2)

        # morph target
        for i, m in enumerate(src.morph_targets):
            morph = dst.get_or_create_morphtarget(i)
            morph.attributes.position[i0] = m[fv0.position_index]
            morph.attributes.position[i1] = m[fv1.position_index]
            morph.attributes.position[i2] = m[fv2.position_index]

        dst = SubmeshMesh.create(src.name, positions, normals, texcoords)

    # submesh
    keys = sorted(material_submesh_map.keys())
    index_offset = 0
    for key in keys:
        s = material_submesh_map[key]
        submesh = Submesh(index_offset, len(s.indices),
                          src.materials[s.material_index])
        index_offset += len(s.indices)
        dst.submeshes.append(submesh)
        dst.indices.extend(s.indices)

    return dst
