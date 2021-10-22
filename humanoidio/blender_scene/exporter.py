from typing import List
import bpy
import bmesh
from ..gltf import exporter


class BlenderObjectExporter:
    def __init__(self):
        self.meshes = []

    def _export_mesh(self, bm):
        triangles = bm.calc_loop_triangles()
        buffer = exporter.ExportMesh(len(bm.verts), len(triangles) * 3)
        self.meshes.append(buffer)

        for i, v in enumerate(bm.verts):
            buffer.POSITION[i] = exporter.Float3(v.co.x, v.co.y, v.co.z)
            buffer.NORMAL[i] = exporter.Float3(v.normal.x, v.normal.y,
                                               v.normal.z)

        i = 0
        for t0, t1, t2 in triangles:
            buffer.indices[i] = t0.index
            i += 1
            buffer.indices[i] = t1.index
            i += 1
            buffer.indices[i] = t2.index
            i += 1

    def _export_object(self, bl_obj: bpy.types.Object):

        if isinstance(bl_obj.data, bpy.types.Mesh):
            bm = bmesh.new()
            bm.from_mesh(bl_obj.data)
            self._export_mesh(bm)
            bm.free()

        for child in bl_obj.children:
            self._export_object(child)

    def export(self, objs: List[bpy.types.Object]):
        for bl_obj in objs:
            export_mesh = self._export_object(bl_obj)
        export_scene = exporter.ExportScene()
        export_scene.meshes = self.meshes
        return export_scene


def export(objs: List[bpy.types.Object]) -> exporter.ExportScene:
    exporter = BlenderObjectExporter()
    return exporter.export(objs)
