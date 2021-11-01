from typing import List
import bpy
from .. import gltf
from .types import bl_obj_gltf_node


class BlenderObjectScanner:
    def __init__(self):
        self.nodes: List[bl_obj_gltf_node] = []

    def _export_mesh(self, bm):
        triangles = bm.calc_loop_triangles()
        buffer = gltf.exporter.ExportMesh(len(bm.verts), len(triangles) * 3)

        for i, v in enumerate(bm.verts):
            buffer.POSITION[i] = gltf.Float3(v.co.x, v.co.y, v.co.z)
            buffer.NORMAL[i] = gltf.Float3(v.normal.x, v.normal.y, v.normal.z)

        i = 0
        for t0, t1, t2 in triangles:
            buffer.indices[i] = t0.vert.index
            i += 1
            buffer.indices[i] = t1.vert.index
            i += 1
            buffer.indices[i] = t2.vert.index
            i += 1

        return buffer

    def _export_object(self, bl_obj: bpy.types.Object):
        node = gltf.Node(bl_obj.name)
        self.nodes.append(bl_obj_gltf_node(bl_obj, node))

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
