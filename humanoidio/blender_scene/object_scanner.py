from typing import List, Tuple
import bpy, mathutils
from .. import gltf
from .types import bl_obj_gltf_node


def vector2float3(v: mathutils.Vector) -> gltf.Float3:
    return gltf.Float3(v.x, v.y, v.z)


def vector2tuple(v: mathutils.Vector) -> Tuple[float, float, float]:
    return (v.x, v.y, v.z)


class BlenderObjectScanner:
    def __init__(self):
        self.nodes: List[bl_obj_gltf_node] = []

    def _export_mesh(self, bm):
        triangles: List[bmesh.types.BMLoop] = bm.calc_loop_triangles()
        buffer = gltf.exporter.ExportMesh(len(bm.verts), len(triangles) * 3)

        for i, v in enumerate(bm.verts):
            buffer.POSITION[i] = vector2float3(v.co)
            buffer.NORMAL[i] = vector2float3(v.normal)

        i = 0
        for t0, t1, t2 in triangles:
            buffer.indices[i] = t0.vert.index
            buffer.loop_normals[i] = vector2float3(t0.calc_normal())
            buffer.check_normal(i)
            i += 1
            buffer.indices[i] = t1.vert.index
            buffer.loop_normals[i] = vector2float3(t1.calc_normal())
            buffer.check_normal(i)
            i += 1
            buffer.indices[i] = t2.vert.index
            buffer.loop_normals[i] = vector2float3(t2.calc_normal())
            buffer.check_normal(i)
            i += 1

        return buffer

    def _export_object(self, bl_obj: bpy.types.Object):
        node = gltf.Node(bl_obj.name)
        self.nodes.append(bl_obj_gltf_node(bl_obj, node))
        node.translation = vector2tuple(bl_obj.location)

        if isinstance(bl_obj.data, bpy.types.Mesh):
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(bl_obj.data)
            node.mesh = self._export_mesh(bm)
            bm.free()

        for child in bl_obj.children:
            child_node = self._export_object(child)
            node.add_child(child_node)

        return node

    def scan(self,
             bl_obj_list: List[bpy.types.Object]) -> List[bl_obj_gltf_node]:
        for bl_obj in bl_obj_list:
            self._export_object(bl_obj)
        return self.nodes


def scan(bl_obj_list: List[bpy.types.Object]) -> List[bl_obj_gltf_node]:
    return BlenderObjectScanner().scan(bl_obj_list)
