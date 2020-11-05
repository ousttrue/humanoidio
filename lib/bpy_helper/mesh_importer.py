import enum
from logging import getLogger
logger = getLogger(__name__)
from typing import Dict, List, Callable
import bpy, mathutils, bmesh
from .. import pyscene

UV0 = 'texcoord0'


def create_bmesh(mesh: pyscene.SubmeshMesh,
                 indicesindex_to_materialindex: Callable[[int], int],
                 yup2zup) -> bmesh.types.BMesh:
    logger.debug(f'create: {mesh}')

    bm = bmesh.new()  # create an empty BMesh

    attributes = mesh.attributes
    for i, v in enumerate(attributes.position):
        # position
        vert = bm.verts.new(yup2zup(v))
        # normal
        if attributes.normal:
            n = attributes.normal[i]
            vert.normal = yup2zup(n)
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
        face.smooth = True  # use vertex normal
        face.material_index = indicesindex_to_materialindex(i)

    # uv
    if uv_layer:
        for face in bm.faces:
            for loop in face.loops:
                uv = attributes.texcoord[loop.vert.index]
                loop[uv_layer].uv = uv.flip_uv()

    # Set morph target positions (no normals/tangents)
    for target in mesh.morphtargets:

        layer = bm.verts.layers.shape.new(target.name)

        for i, vert in enumerate(bm.verts):
            p = target.attributes.position[i]
            vert[layer] = mathutils.Vector(yup2zup(p)) + vert.co

    return bm
