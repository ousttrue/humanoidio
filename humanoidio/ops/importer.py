from logging import getLogger
from typing import Tuple

logger = getLogger(__name__)

import bpy
from bpy_extras.io_utils import ImportHelper
import pathlib
from .. import gltf
from .. import blender_scene
from .. import mmd


def z_reverse(x, y, z):
    return (x, y, -z)


def pmx_to_gltf(pmx: mmd.pmx_loader.Pmx) -> gltf.Loader:
    '''
    model
      mesh
      root
    '''

    loader = gltf.Loader()

    # create bones
    for b in pmx.bones:
        node = gltf.Node(b.name_ja)
        # world pos
        node.translation = z_reverse(b.position.x, b.position.y, b.position.z)
        loader.nodes.append(node)

    # build tree
    for i, b in enumerate(pmx.bones):
        if b.parent_index == -1:
            # root
            loader.roots.append(loader.nodes[i])
        else:
            parent = loader.nodes[b.parent_index]
            parent.add_child(loader.nodes[i])

    mesh_node = gltf.Node('__mesh__')
    mesh_node.mesh = gltf.Mesh('mesh')
    offset = 0
    mesh_node.mesh.vertices = gltf.VertexBuffer()

    def pos_gen():
        it = iter(pmx.vertices)
        while True:
            try:
                v = next(it)
                yield z_reverse(v.position.x, v.position.y, v.position.z)
            except StopIteration:
                break

    def normal_gen():
        it = iter(pmx.vertices)
        while True:
            try:
                v = next(it)
                yield z_reverse(v.normal.x, v.normal.y, v.normal.z)
            except StopIteration:
                break

    def joint_gen():
        it = iter(pmx.vertices)
        while True:
            try:
                v = next(it)
                yield (int(v.bone.x), int(v.bone.y), int(v.bone.z),
                       int(v.bone.w))
            except StopIteration:
                break

    def weight_gen():
        it = iter(pmx.vertices)
        while True:
            try:
                v = next(it)
                yield (v.weight.x, v.weight.y, v.weight.z, v.weight.w)
            except StopIteration:
                break

    mesh_node.mesh.vertices.POSITION = pos_gen
    mesh_node.mesh.vertices.NORMAL = normal_gen
    mesh_node.mesh.vertices.JOINTS_0 = joint_gen
    mesh_node.mesh.vertices.WEIGHTS_0 = weight_gen

    it = iter(pmx.indices)
    for submesh in pmx.submeshes:
        gltf_submesh = gltf.Submesh(offset, submesh.draw_count)

        def indices_gen():
            while True:
                try:
                    i = next(it)
                    yield i
                except StopIteration:
                    break

        gltf_submesh.indices = indices_gen
        mesh_node.mesh.submeshes.append(gltf_submesh)
        offset += submesh.draw_count
    mesh_node.skin = gltf.Skin()
    mesh_node.skin.joints = [node for node in loader.nodes]
    loader.nodes.append(mesh_node)
    loader.roots.append(mesh_node)

    def relative(parent: gltf.Node, parent_pos: Tuple[float, float, float]):
        # print(parent.name, parent.translation)
        for child in parent.children:
            child_pos = child.translation

            child.translation = (child_pos[0] - parent_pos[0],
                                 child_pos[1] - parent_pos[1],
                                 child_pos[2] - parent_pos[2])

            relative(child, child_pos)

    for root in loader.roots:
        relative(root, root.translation)

    return loader


class Importer(bpy.types.Operator, ImportHelper):
    bl_idname = "humanoidio.importer"
    bl_label = "humanoidio Importer"

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')
        # read file
        path = pathlib.Path(self.filepath).absolute()
        ext = path.suffix.lower()
        if ext == '.pmx':
            pmx = mmd.load(path)
            conversion = gltf.Conversion(gltf.Coordinate.VRM1,
                                         gltf.Coordinate.BLENDER_ROTATE)
            # print(loaded)
            loader = pmx_to_gltf(pmx)

        else:
            loader, conversion = gltf.load(path,
                                           gltf.Coordinate.BLENDER_ROTATE)

        # build mesh
        collection = bpy.data.collections.new(name=path.name)
        context.scene.collection.children.link(collection)
        bl_importer = blender_scene.Importer(collection, conversion)
        bl_importer.load(loader)

        logger.debug('#### end ####')
        return {'FINISHED'}


def menu(self, context):
    self.layout.operator(Importer.bl_idname,
                         text=f"humanoidio (.gltf;.glb;.vrm;.pmx)")
