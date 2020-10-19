from logging import getLogger
logger = getLogger(__name__)
from typing import List, Optional, Dict
import bpy, mathutils
from . import disposable_mode
from ..yup.node import Node
from ..yup.submesh_mesh import SubmeshMesh

# def mod_v(v):
#     return (v[0], -v[2], v[1])

# def mod_q(q):
#     return mathutils.Quaternion(mod_v(q.axis), q.angle)


class Importer:
    def __init__(self, context: bpy.types.Context):
        view_layer = context.view_layer
        if hasattr(view_layer,
                   'collections') and view_layer.collections.active:
            self.collection = view_layer.collections.active.collection
        else:
            self.collection = context.scene.collection
            # view_layer.collections.link(collection)

        self.obj_map: Dict[Node, bpy.types.Object] = {}
        self.mesh_map: Dict[SubmeshMesh, bpy.types.Mesh] = {}

    def _create_object(self, node: Node) -> None:
        '''
        Node から bpy.types.Object を作る
        '''
        logger.debug(f'create: {node}')

        # create object
        if isinstance(node.mesh, SubmeshMesh):
            obj = bpy.data.objects.new(node.name, self.mesh_map.get(node.mesh))
        else:
            # empty
            obj = bpy.data.objects.new(node.name, None)
            obj.empty_display_size = 0.1
            # self.blender_object.empty_draw_type = 'PLAIN_AXES'
        self.collection.objects.link(obj)
        obj.select_set(True)
        self.obj_map[node] = obj

        # parent
        if node.parent:
            obj.parent = self.obj_map.get(node.parent)

        # TRS
        # obj.location = node.position
        # with disposable_mode(obj, 'QUATERNION'):
        #     obj.rotation_quaternion = node.rotation
        # obj.scale = node.scale

    def traverse(self, node: Node, parent: Optional[Node] = None):
        self._create_object(node)
        for child in node.children:
            self.traverse(child, node)


def import_roots(context: bpy.types.Context, roots: List[Node]):
    importer = Importer(context)
    for root in roots:
        importer.traverse(root)

    # manager = ImportManager()
    # manager.load_textures()
    # manager.load_materials()
    # manager.load_meshes()
    # for m, _ in manager.meshes:
    #     logger.debug(f'[{m.name}: {len(m.vertices)}]vertices')
    # nodes, root = manager.load_objects(context, roots)

    # # skinning
    # armature_object = next(node for node in root.traverse()
    #                         if node.blender_armature)

    # for node in nodes:
    #     if node.gltf_node.mesh != -1 and node.gltf_node.skin != -1:
    #         _, attributes = manager.meshes[node.gltf_node.mesh]

    #         skin = gltf.skins[node.gltf_node.skin]
    #         bone_names = [nodes[joint].bone_name for joint in skin.joints]

    #         #armature_object =nodes[skin.skeleton].blender_armature

    #         _setup_skinning(obj, attributes, bone_names,
    #                         armature_object.blender_armature)

    # remove empties
    # _remove_empty(root)

    # done
    # context.scene.update()
