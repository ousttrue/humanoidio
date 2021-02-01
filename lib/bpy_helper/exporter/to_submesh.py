import enum
from typing import List, Dict, NamedTuple
from ...struct_types import Float2, Float3, Float4, UShort4
from ...pyscene import Node, FaceMesh, Submesh, SubmeshMesh, Vertex


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
        vertices = [Vertex.zero()] * len(src.positions)
    else:
        vertices = []

    dst = SubmeshMesh(src.name)

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

        b0 = src.bone_weights[fv0.position_index]
        b1 = src.bone_weights[fv1.position_index]
        b2 = src.bone_weights[fv2.position_index]

        v0 = Vertex(p0, n0, uv0, b0.joints, b0.weights)
        v1 = Vertex(p1, n1, uv1, b1.joints, b1.weights)
        v2 = Vertex(p2, n2, uv2, b2.joints, b2.weights)

        if src.is_face_splitted():
            # Faceが分離済み(positions と face_vertices が一致)
            # 頂点 index が維持される
            i0 = fv0.position_index
            i1 = fv1.position_index
            i2 = fv2.position_index
            vertices[i0] = v0
            vertices[i1] = v1
            vertices[i2] = v2
        else:
            # 頂点 index の振り直し
            i0 = len(vertices)
            vertices.append(v0)
            i1 = len(vertices)
            vertices.append(v1)
            i2 = len(vertices)
            vertices.append(v2)

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

    dst.set_vertices(vertices)

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
