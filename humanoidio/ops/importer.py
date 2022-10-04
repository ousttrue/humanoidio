from logging import getLogger
from typing import Tuple

logger = getLogger(__name__)

import bpy
from bpy_extras.io_utils import ImportHelper
import pathlib
from .. import gltf
from .. import blender_scene
from .. import mmd


def pmx_to_gltf(pmx: mmd.pmx_loader.Pmx, scale=1.52 / 20) -> gltf.Loader:
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
        node.translation = (b.position.x, b.position.y, b.position.z)
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
    for submesh in pmx.submeshes:
        gltf_submesh = gltf.Submesh(offset, submesh.draw_count)
        # def position():
        #     for v in pmx.vertices:
        #         v.
        #     return [v.position for v in pmx.vertices]
        # gltf_submesh.POSITION = position
        # # gltf_submesh.NORMAL: Optional[Generator[Any, None, None]] = None
        # gltf_submesh.indices = pmx.indices[offset:offset + submesh.draw_count]
        mesh_node.mesh.submeshes.append(gltf_submesh)
        offset += submesh.draw_count
    mesh_node.skin = gltf.Skin()
    mesh_node.skin.joints = [node for node in loader.nodes]
    loader.nodes.append(mesh_node)
    loader.roots.append(mesh_node)

    def relative(parent: gltf.Node, parent_pos: Tuple[float, float, float]):
        print(parent.name, parent.translation)
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
            conversion = gltf.Conversion(gltf.Coodinate.VRM1,
                                         gltf.Coodinate.BLENDER_ROTATE)
            # print(loaded)
            loader = pmx_to_gltf(pmx)

        else:
            loader, conversion = gltf.load(path, gltf.Coodinate.BLENDER_ROTATE)

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