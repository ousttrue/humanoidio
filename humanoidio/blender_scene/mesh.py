import bpy
import bmesh
from .. import gltf

UV_LAYER_NAME = 'texcoord0'
DEFORM_LAYER_NAME = 'deform0'


def create_vertices(bm, vertex_buffer: gltf.VertexBuffer):

    deform_layer = None
    if vertex_buffer.JOINTS_0:
        deform_layer = bm.verts.layers.deform

    for pos, n, j, w in vertex_buffer.get_vertices():
        # position
        vert = bm.verts.new(pos)
        # normal
        if n:
            vert.normal = n
        # bone weight
        if deform_layer:
            vert[deform_layer][j] = w


def create_face(bm, mesh: gltf.Submesh):
    for i0, i1, i2 in mesh.get_indices():
        v0 = bm.verts[i0 + mesh.vertex_offset]
        v1 = bm.verts[i1 + mesh.vertex_offset]
        v2 = bm.verts[i2 + mesh.vertex_offset]
        face = bm.faces.new((v0, v1, v2))
        face.smooth = True  # use vertex normal
        # face.material_index = indicesindex_to_materialindex(i)


def get_or_create_uv_layer(bm):
    if UV_LAYER_NAME in bm.loops.layers.uv:
        return bm.loops.layers.uv[UV_LAYER_NAME]
    return bm.loops.layers.uv.new(UV_LAYER_NAME)


def set_uv(bm, uv_list):
    uv_layer = get_or_create_uv_layer(bm)
    for face in bm.faces:
        for loop in face.loops:
            uv = uv_list[loop.vert.index]
            loop[uv_layer].uv = uv

    # # Set morph target positions (no normals/tangents)
    # for target in mesh.morphtargets:

    #     layer = bm.verts.layers.shape.new(target.name)

    #     for i, vert in enumerate(bm.verts):
    #         p = target.attributes.position[i]
    #         vert[layer] = mathutils.Vector(yup2zup(p)) + vert.co


def create_mesh(bl_mesh: bpy.types.Mesh, mesh: gltf.Mesh):
    # create an empty BMesh
    bm = bmesh.new()

    uv_list = []

    # vertices
    if mesh.vertices:
        create_vertices(bm, mesh.vertices)
        tex = mesh.vertices.TEXCOORD_0
        if tex:
            for uv in tex():
                uv_list.append(uv)
    else:
        for sm in mesh.submeshes:
            create_vertices(bm, sm.vertices)
            tex = sm.vertices.TEXCOORD_0
            if tex:
                for uv in tex():
                    uv_list.append(uv)

    bm.verts.ensure_lookup_table()
    bm.verts.index_update()

    # triangles
    for sm in mesh.submeshes:
        create_face(bm, sm)

    # loop layer
    if len(uv_list) > 0:
        set_uv(bm, uv_list)

    bm.to_mesh(bl_mesh)
    bm.free()
