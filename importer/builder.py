import json
import pathlib
from typing import Set, List
import bpy
from ..formats.glb import Glb
from ..formats.gltf import glTF

from .import_manager import ImportManager
from .texture_io import load_textures
from .material_io import load_materials
from .mesh_io import load_meshes
from .node_io import load_objects
from .node import Node
# from . import gltf_buffer

from logging import getLogger  # pylint: disable=C0411
logger = getLogger(__name__)

# def _setup_skinning(blender_object: bpy.types.Object,
#                     attributes: gltf_buffer.VertexBuffer,
#                     bone_names: List[str],
#                     armature_object: bpy.types.Object) -> None:
#     # create vertex groups
#     for bone_name in bone_names:
#         if bone_name:
#             blender_object.vertex_groups.new(name=bone_name)

#     idx_already_done: Set[int] = set()

#     # each face
#     for poly in blender_object.data.polygons:
#         # face vertex index
#         for loop_idx in range(poly.loop_start,
#                               poly.loop_start + poly.loop_total):
#             loop = blender_object.data.loops[loop_idx]
#             vert_idx = loop.vertex_index
#             if vert_idx < 0:
#                 raise Exception()
#             if vert_idx >= len(attributes.joints):
#                 raise Exception()

#             if vert_idx in idx_already_done:
#                 continue
#             idx_already_done.add(vert_idx)

#             cpt = 0
#             for joint_idx in attributes.joints[vert_idx]:
#                 if cpt > 3:
#                     break
#                 weight_val = attributes.weights[vert_idx][cpt]
#                 if weight_val != 0.0:
#                     # It can be a problem to assign weights of 0
#                     # for bone index 0, if there is always 4 indices in joint_ tuple
#                     bone_name = bone_names[joint_idx]
#                     if bone_name:
#                         group = blender_object.vertex_groups[bone_name]
#                         group.add([vert_idx], weight_val, 'REPLACE')
#                 cpt += 1

#     # select
#     # for obj_sel in bpy.context.scene.objects:
#     #    obj_sel.select = False
#     #blender_object.select = True
#     #bpy.context.scene.objects.active = blender_object

#     modifier = blender_object.modifiers.new(name="Armature", type="ARMATURE")
#     modifier.object = armature_object


def _remove_empty(node: Node):
    for i in range(len(node.children) - 1, -1, -1):
        child = node.children[i]
        _remove_empty(child)

    if node.children:
        # print(f'{node} children {len(node.children)}')
        return
    if node.blender_armature:
        # print(f'{node} has {node.blender_armature}')
        return
    if node.blender_object.data:
        # print(f'{node} has {node.blender_object}')
        return

    # remove empty
    print('remove', node)
    bpy.data.objects.remove(node.blender_object, do_unlink=True)
    if node.parent:
        node.parent.children.remove(node)


def load(context: bpy.types.Context, filepath: str) -> Set[str]:

    path = pathlib.Path(filepath)
    if not path.exists():
        return {'CANCELLED'}

    body = b''
    try:
        with path.open('rb') as f:
            ext = path.suffix.lower()
            if ext == '.gltf':
                gltf = glTF.from_dict(json.load(f))
            elif ext == '.glb' or ext == '.vrm':
                glb = Glb.from_bytes(f.read())
                gltf = glTF.from_dict(json.loads(glb.json))
                body = glb.bin
            else:
                logger.error("%s is not supported", ext)
                return {'CANCELLED'}
    except Exception as ex:  # pylint: disable=w0703
        logger.error("%s", ex)
        return {'CANCELLED'}

    manager = ImportManager(path, gltf, body)
    manager.textures.extend(load_textures(manager))
    manager.materials.extend(load_materials(manager))
    manager.meshes.extend(load_meshes(manager))
    for m, _ in manager.meshes:
        print(f'[{m.name}: {len(m.vertices)}]vertices')
    nodes, root = load_objects(context, manager)

    # # skinning
    # armature_object = next(node for node in root.traverse()
    #                         if node.blender_armature)

    # for node in nodes:
    #     if node.gltf_node.mesh != -1 and node.gltf_node.skin != -1:
    #         _, attributes = manager.meshes[node.gltf_node.mesh]

    #         skin = gltf.skins[node.gltf_node.skin]
    #         bone_names = [nodes[joint].bone_name for joint in skin.joints]

    #         #armature_object =nodes[skin.skeleton].blender_armature

    #         _setup_skinning(node.blender_object, attributes, bone_names,
    #                         armature_object.blender_armature)

    # remove empties
    _remove_empty(root)

    # done
    # context.scene.update()

    return {'FINISHED'}
