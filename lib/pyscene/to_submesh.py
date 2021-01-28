import enum
from typing import List, Dict
from ..struct_types import Float2
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

    if src.is_face_splitted():
        # Faceが分離済み(positions と face_vertices が一致)
        # 三角形を頂点バッファに展開する
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

        dst = SubmeshMesh(src.name, len(src.positions), has_bone_weight=False)

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

            dst.attributes.set_vertex(fv0.position_index, p0, n0, uv0)
            dst.attributes.set_vertex(fv1.position_index, p1, n1, uv1)
            dst.attributes.set_vertex(fv2.position_index, p2, n2, uv2)
            submesh = get_or_create_submesh(t.material_index)
            submesh.indices.append(fv0.position_index)
            submesh.indices.append(fv1.position_index)
            submesh.indices.append(fv2.position_index)

            # morph target
            for i, m in enumerate(src.morph_targets):
                morph = dst.get_or_create_morphtarget(i)
                morph.attributes.position[fv0.position_index] = m[
                    fv0.position_index]
                morph.attributes.position[fv1.position_index] = m[
                    fv1.position_index]
                morph.attributes.position[fv2.position_index] = m[
                    fv2.position_index]

    else:
        # ToDo: 三角形化？
        raise Exception()

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
