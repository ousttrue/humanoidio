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

    def _get_or_create_mesh(self, mesh: SubmeshMesh) -> bpy.types.Mesh:
        bl_mesh = self.mesh_map.get(mesh)
        if bl_mesh:
            return bl_mesh

        bl_mesh = bpy.data.meshes.new(mesh.name)

        # materials = [manager.materials[prim.material] for prim in bl_mesh.primitives]
        # for m in materials:
        #     bl_mesh.materials.append(m)

        attributes = mesh.attributes

        bl_mesh.vertices.add(attributes.get_vertex_count())
        bl_mesh.vertices.foreach_set(
            "co", [n for v in attributes.position for n in (v.x, v.y, v.z)])
        bl_mesh.vertices.foreach_set(
            "normal", [n for v in attributes.normal for n in (v.x, v.y, v.z)])

        bl_mesh.loops.add(len(mesh.indices))
        bl_mesh.loops.foreach_set("vertex_index", mesh.indices)

        triangle_count = len(mesh.indices) // 3
        bl_mesh.polygons.add(triangle_count)
        starts = [i * 3 for i in range(triangle_count)]
        bl_mesh.polygons.foreach_set("loop_start", starts)
        total = [3 for _ in range(triangle_count)]
        bl_mesh.polygons.foreach_set("loop_total", total)

        # blen_uvs = bl_mesh.uv_layers.new()
        # for blen_poly in bl_mesh.polygons:
        #     blen_poly.use_smooth = True
        #     blen_poly.material_index = attributes.get_submesh_from_face(
        #         blen_poly.index)
        #     for lidx in blen_poly.loop_indices:
        #         index = attributes.indices[lidx]
        #         # vertex uv to face uv
        #         uv = attributes.uv[index]
        #         blen_uvs.data[lidx].uv = (uv.x, uv.y)  # vertical flip uv

        # *Very* important to not remove lnors here!
        bl_mesh.validate(clean_customdata=False)
        bl_mesh.update()

        self.mesh_map[mesh] = bl_mesh
        return bl_mesh

    def _create_object(self, node: Node) -> None:
        '''
        Node から bpy.types.Object を作る
        '''
        logger.debug(f'create: {node}')

        # create object
        if isinstance(node.mesh, SubmeshMesh):
            bl_mesh = self._get_or_create_mesh(node.mesh)
            bl_obj = bpy.data.objects.new(node.name, bl_mesh)
        else:
            # empty
            bl_obj = bpy.data.objects.new(node.name, None)
            bl_obj.empty_display_size = 0.1
            # self.blender_object.empty_draw_type = 'PLAIN_AXES'
        self.collection.objects.link(bl_obj)
        bl_obj.select_set(True)
        self.obj_map[node] = bl_obj

        # parent
        if node.parent:
            bl_obj.parent = self.obj_map.get(node.parent)

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
