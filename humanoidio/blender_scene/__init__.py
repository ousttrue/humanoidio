from logging import getLogger

logger = getLogger(__name__)

import bpy
import bmesh
from .. import gltf


def create_vertices(bm, mesh: gltf.Submesh):
    for pos, n in mesh.get_vertices():
        # position
        vert = bm.verts.new(pos)
        # normal
        if n:
            vert.normal = n


def create_face(bm, mesh: gltf.Submesh):
    for i0, i1, i2 in mesh.get_indices():
        v0 = bm.verts[i0 + mesh.vertex_offset]
        v1 = bm.verts[i1 + mesh.vertex_offset]
        v2 = bm.verts[i2 + mesh.vertex_offset]
        face = bm.faces.new((v0, v1, v2))
        face.smooth = True  # use vertex normal
        # face.material_index = indicesindex_to_materialindex(i)

    # uv_layer = None
    # if attributes.texcoord:
    #     uv_layer = bm.loops.layers.uv.new(UV0)
    # # uv
    # if uv_layer:
    #     for face in bm.faces:
    #         for loop in face.loops:
    #             uv = attributes.texcoord[loop.vert.index]
    #             loop[uv_layer].uv = uv.flip_uv()

    # # Set morph target positions (no normals/tangents)
    # for target in mesh.morphtargets:

    #     layer = bm.verts.layers.shape.new(target.name)

    #     for i, vert in enumerate(bm.verts):
    #         p = target.attributes.position[i]
    #         vert[layer] = mathutils.Vector(yup2zup(p)) + vert.co


def load(loader: gltf.Loader):
    for mesh in loader.meshes:
        logger.debug(f'create: {mesh.name}')

        # create an empty BMesh
        bm = bmesh.new()
        for i, sm in enumerate(mesh.submeshes):
            create_vertices(bm, sm)

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        for i, sm in enumerate(mesh.submeshes):
            create_face(bm, sm)

        # Create an empty mesh and the object.
        name = mesh.name
        bl_mesh = bpy.data.meshes.new(name + '_mesh')
        bl_obj = bpy.data.objects.new(name, bl_mesh)
        # Add the object into the scene.
        bpy.context.scene.collection.objects.link(bl_obj)

        bm.to_mesh(bl_mesh)
        bm.free()
