from logging import getLogger
logger = getLogger(__name__)
from contextlib import contextmanager
from typing import List, Optional, Dict, Set
import bpy, mathutils
from ..pyscene.node import Node, Skin
from ..pyscene.submesh_mesh import SubmeshMesh
from ..pyscene.material import Material
from .material_importer import MaterialImporter


def mod_v(v):
    return (v[0], -v[2], v[1])


def mod_q(_q):
    q = mathutils.Quaternion((_q.w, _q.x, _q.y, _q.z))
    return mathutils.Quaternion(mod_v(q.axis), q.angle)


def mod_s(s):
    return (s[0], s[2], s[1])


@contextmanager
def tmp_mode(obj, tmp: str):
    mode = obj.rotation_mode
    obj.rotation_mode = tmp
    try:
        yield
    finally:
        obj.rotation_mode = mode


class Importer:
    '''
    bpy.types.Object, Mesh, Material, Texture を作成する
    '''
    def __init__(self, context: bpy.types.Context):
        self.context = context
        view_layer = context.view_layer
        if hasattr(view_layer,
                   'collections') and view_layer.collections.active:
            self.collection = view_layer.collections.active.collection
        else:
            self.collection = context.scene.collection
            # view_layer.collections.link(collection)

        self.obj_map: Dict[Node, bpy.types.Object] = {}
        self.mesh_map: Dict[SubmeshMesh, bpy.types.Mesh] = {}
        self.material_importer = MaterialImporter()
        self.skin_map: Dict[Skin, bpy.types.Object] = {}

    def _setup_skinning(self, mesh_node: Node) -> None:
        if not isinstance(mesh_node.mesh, SubmeshMesh):
            return
        if not mesh_node.skin:
            return

        skin = mesh_node.skin
        bone_names = [joint.name for joint in skin.joints]
        bl_object = self.obj_map[mesh_node]

        # create vertex groups
        for bone_name in bone_names:
            if bone_name:
                bl_object.vertex_groups.new(name=bone_name)

        idx_already_done: Set[int] = set()

        attributes = mesh_node.mesh.attributes

        # each face
        for poly in bl_object.data.polygons:
            # face vertex index
            for loop_idx in range(poly.loop_start,
                                  poly.loop_start + poly.loop_total):
                loop = bl_object.data.loops[loop_idx]
                vert_idx = loop.vertex_index
                if vert_idx < 0:
                    raise Exception()
                if vert_idx >= len(attributes.joints):
                    raise Exception()

                if vert_idx in idx_already_done:
                    continue
                idx_already_done.add(vert_idx)

                cpt = 0
                for joint_idx in attributes.joints[vert_idx]:
                    if cpt > 3:
                        break
                    weight_val = attributes.weights[vert_idx][cpt]
                    if weight_val != 0.0:
                        # It can be a problem to assign weights of 0
                        # for bone index 0, if there is always 4 indices in joint_ tuple
                        bone_name = bone_names[joint_idx]
                        if bone_name:
                            group = bl_object.vertex_groups[bone_name]
                            group.add([vert_idx], weight_val, 'REPLACE')
                    cpt += 1

        modifier = bl_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = self.skin_map[skin]

    def _create_armature(self, node: Node, skin: Skin) -> bpy.types.Object:
        logger.debug(f'skin')
        bl_skin: bpy.types.Armature = bpy.data.armatures.new(skin.name)
        bl_obj = bpy.data.objects.new(skin.name, bl_skin)
        self.skin_map[skin] = bl_obj
        bl_obj.show_in_front = True
        self.collection.objects.link(bl_obj)

        if skin.root:
            bl_obj.parent = self.obj_map[skin.root]

        self.context.view_layer.objects.active = bl_obj
        bl_obj.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # set identity matrix_world to armature
        m = mathutils.Matrix()
        m.identity()
        bl_obj.matrix_world = m
        # self.context.scene.update()  # recalc matrix_world

        # create bones
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        self._create_bone(bl_skin, skin.root, None, False)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    def _create_bone(self, armature: bpy.types.Armature, node: Node,
                     parent_bone: Optional[bpy.types.Bone],
                     is_connect: bool) -> None:

        logger.debug(node.name)
        bl_bone = armature.edit_bones.new(node.name)
        bl_bone.parent = parent_bone
        if is_connect:
            bl_bone.use_connect = True

        bl_object = self.obj_map[node]
        object_pos = bl_object.matrix_world.to_translation()
        bl_bone.head = object_pos

        if not is_connect:
            if parent_bone and parent_bone.tail == (0, 0, 0):
                tail_offset = (bl_bone.head -
                               parent_bone.head).normalized() * 0.1
                parent_bone.tail = parent_bone.head + tail_offset

        if not node.children:
            if parent_bone:
                bl_bone.tail = bl_bone.head + \
                    (bl_bone.head - parent_bone.head)
        else:

            def get_child_is_connect(child_pos) -> bool:
                if len(node.children) == 1:
                    return True

                if abs(child_pos.x) < 0.001:
                    return True

                return False

            if parent_bone:
                child_is_connect = 0
                for i, child in enumerate(node.children):
                    if get_child_is_connect(
                            self.obj_map[child].matrix_world.to_translation()):
                        child_is_connect = i
            else:
                child_is_connect = -1

            for i, child in enumerate(node.children):
                self._create_bone(armature, child, bl_bone,
                                  i == child_is_connect)

    def _get_or_create_mesh(self, mesh: SubmeshMesh) -> bpy.types.Mesh:
        bl_mesh = self.mesh_map.get(mesh)
        if bl_mesh:
            return bl_mesh

        bl_mesh = bpy.data.meshes.new(mesh.name)
        self.mesh_map[mesh] = bl_mesh

        material_index_map: Dict[Material, int] = {}
        material_index = 0
        for submesh in mesh.submeshes:
            bl_material = self.material_importer.get_or_create_material(
                submesh.material)
            bl_mesh.materials.append(bl_material)
            material_index_map[submesh.material] = material_index
            material_index += 1

        # vertices
        attributes = mesh.attributes
        bl_mesh.vertices.add(attributes.get_vertex_count())
        bl_mesh.vertices.foreach_set(
            "co", [n for v in attributes.position for n in (v.x, -v.z, v.y)])
        bl_mesh.vertices.foreach_set(
            "normal", [n for v in attributes.normal for n in (v.x, -v.z, v.y)])

        # indices
        bl_mesh.loops.add(len(mesh.indices))
        bl_mesh.loops.foreach_set("vertex_index", mesh.indices)

        # face
        triangle_count = len(mesh.indices) // 3
        bl_mesh.polygons.add(triangle_count)
        starts = [i * 3 for i in range(triangle_count)]
        bl_mesh.polygons.foreach_set("loop_start", starts)
        total = [3 for _ in range(triangle_count)]
        bl_mesh.polygons.foreach_set("loop_total", total)
        # uv
        bl_texcord = bl_mesh.uv_layers.new()
        submesh_index = 0
        submesh_count = 0
        tmp = []
        for bl_poly in bl_mesh.polygons:
            if submesh_count >= mesh.submeshes[submesh_index].vertex_count:
                submesh_index += 1
                submesh_count = 0
            bl_poly.use_smooth = True  # enable vertex normal
            bl_poly.material_index = material_index_map.get(
                mesh.submeshes[submesh_index].material)
            for lidx in bl_poly.loop_indices:
                tmp.append(lidx)
                vertex_index = mesh.indices[lidx]
                # vertex uv to face uv
                uv = attributes.texcoord[vertex_index]
                bl_texcord.data[lidx].uv = (uv.x, 1.0 - uv.y)  # vertical flip uv
            submesh_count += 3

        # *Very* important to not remove lnors here!
        bl_mesh.validate(clean_customdata=False)
        bl_mesh.update()

        return bl_mesh

    def _create_object(self, node: Node) -> None:
        '''
        Node から bpy.types.Object を作る
        '''
        logger.debug(f'create: {node}')

        # create object
        if isinstance(node.mesh, SubmeshMesh):
            bl_mesh = self._get_or_create_mesh(node.mesh)
            bl_obj: bpy.types.Object = bpy.data.objects.new(node.name, bl_mesh)
        else:
            # empty
            bl_obj: bpy.types.Object = bpy.data.objects.new(node.name, None)
            bl_obj.empty_display_size = 0.1
            # bl_object.empty_draw_type = 'PLAIN_AXES'
        self.collection.objects.link(bl_obj)
        bl_obj.select_set(True)
        self.obj_map[node] = bl_obj

        # parent
        if node.parent:
            bl_obj.parent = self.obj_map.get(node.parent)

        # TRS
        bl_obj.location = mod_v(node.position)
        with tmp_mode(bl_obj, 'QUATERNION'):
            bl_obj.rotation_quaternion = mod_q(node.rotation)
        bl_obj.scale = mod_s(node.scale)

    def _create_tree(self, node: Node, parent: Optional[Node] = None):
        self._create_object(node)
        for child in node.children:
            self._create_tree(child, node)

    def _remove_empty(self, node: Node):
        '''
        深さ優先で、深いところから順に削除する
        '''
        for i in range(len(node.children) - 1, -1, -1):
            child = node.children[i]
            self._remove_empty(child)

        if node.children:
            return
        if node.mesh:
            return
        for skin, v in self.skin_map.items():
            if skin.root == node:
                bl_parent = self.obj_map[node]
                bl_skin = self.skin_map[skin]
                tmp = bl_skin.matrix_world
                bl_skin.parent = bl_parent.parent               
                bpy.data.objects.remove(bl_parent, do_unlink=True)
                bl_skin.matrix_world = tmp
                return

        # remove empty
        logger.debug(f'remove: {node}')
        bl_obj = self.obj_map[node]
        bpy.data.objects.remove(bl_obj, do_unlink=True)
        if node.parent:
            node.parent.children.remove(node)

    def execute(self, roots: List[Node]):
        for root in roots:
            self._create_tree(root)

        # skinning
        for root in roots:
            for skin_node in root.traverse():
                if skin_node.skin:
                    self._create_armature(skin_node, skin_node.skin)

        for n, o in self.obj_map.items():
            if o.type == 'MESH' and n.skin:
                self._setup_skinning(n)

        # remove empties
        for root in roots:
            self._remove_empty(root)
