from typing import Dict, List
import bpy, mathutils, bmesh
from .. import pyscene

UV0 = 'texcoord0'


def create_bmesh(mesh: pyscene.SubmeshMesh):
    bm = bmesh.new()  # create an empty BMesh

    attributes = mesh.attributes
    for i, v in enumerate(attributes.position):
        # position
        vert = bm.verts.new((v.x, -v.z, v.y))
        # normal
        if attributes.normal:
            n = attributes.normal[i]
            vert.normal = (n.x, -n.z, n.y)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()

    uv_layer = None
    if attributes.texcoord:
        uv_layer = bm.loops.layers.uv.new(UV0)

    # face
    for i in range(0, len(mesh.indices), 3):
        i0 = mesh.indices[i]
        i1 = mesh.indices[i + 1]
        i2 = mesh.indices[i + 2]
        v0 = bm.verts[i0]
        v1 = bm.verts[i1]
        v2 = bm.verts[i2]
        face = bm.faces.new((v0, v1, v2))
        face.smooth = True

    # uv
    if uv_layer:
        for face in bm.faces:
            for loop in face.loops:
                uv = attributes.texcoord[loop.vert.index]
                loop[uv_layer].uv = (uv.x, 1 - uv.y)

    # bl_mesh.vertices.add(attributes.get_vertex_count())
    # bl_mesh.vertices.foreach_set(
    #     "co", [n for v in attributes.position for n in (v.x, -v.z, v.y)])
    # bl_mesh.vertices.foreach_set(
    #     "normal", [n for v in attributes.normal for n in (v.x, -v.z, v.y)])

    # # indices
    # bl_mesh.loops.add(len(mesh.indices))
    # bl_mesh.loops.foreach_set("vertex_index", mesh.indices)

    # # face
    # triangle_count = len(mesh.indices) // 3
    # bl_mesh.polygons.add(triangle_count)
    # starts = [i * 3 for i in range(triangle_count)]
    # bl_mesh.polygons.foreach_set("loop_start", starts)
    # total = [3 for _ in range(triangle_count)]
    # bl_mesh.polygons.foreach_set("loop_total", total)
    # # uv
    # bl_texcord = bl_mesh.uv_layers.new()
    # submesh_index = 0
    # submesh_count = 0
    # tmp = []
    # for bl_poly in bl_mesh.polygons:
    #     if submesh_count >= mesh.submeshes[submesh_index].vertex_count:
    #         submesh_index += 1
    #         submesh_count = 0
    #     bl_poly.use_smooth = True  # enable vertex normal
    #     bl_poly.material_index = material_index_map.get(
    #         mesh.submeshes[submesh_index].material)
    #     for lidx in bl_poly.loop_indices:
    #         tmp.append(lidx)
    #         vertex_index = mesh.indices[lidx]
    #         # vertex uv to face uv
    #         uv = attributes.texcoord[vertex_index]
    #         bl_texcord.data[lidx].uv = (uv.x, 1.0 - uv.y)  # vertical flip uv
    #     submesh_count += 3

    return bm
