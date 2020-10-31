from mathutils import Vector
from logging import getLogger
logger = getLogger(__name__)
from contextlib import contextmanager
from typing import List, Optional, Dict, Set
import bpy, mathutils
from .. import pyscene
from .. import formats
from .material_importer import MaterialImporter
from .mesh_importer import create_bmesh
from .functions import remove_mesh


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


class BoneConnector:
    '''
    ボーンを適当に接続したり、しない場合でも tail を設定してやる
    '''
    def __init__(self, bones: Dict[pyscene.Node, bpy.types.EditBone]):
        self.bones = bones

    def extend_tail(self, node: pyscene.Node):
        '''
        親ボーンと同じ方向にtailを延ばす
        '''
        bl_bone = self.bones[node]
        if node.parent:
            bl_parent = self.bones[node.parent]
            tail_offset = (bl_bone.head - bl_parent.head)
            bl_bone.tail = bl_bone.head + tail_offset

    def connect_tail(self, node: pyscene.Node, tail: pyscene.Node):
        bl_bone = self.bones[node]
        bl_tail = self.bones[tail]
        bl_bone.tail = bl_tail.head
        bl_tail.parent = bl_bone
        bl_tail.use_connect = True

    def traverse(self, node: pyscene.Node, parent: Optional[pyscene.Node],
                 is_connect: bool):
        # connect
        if parent:
            # print(f'connect {parent} => {node}')
            bl_parent = self.bones[parent]
            bl_bone = self.bones[node]
            bl_bone.parent = bl_parent
            if is_connect:
                bl_parent.tail = bl_bone.head
                bl_bone.use_connect = True

        if node.children:
            # recursive
            connect_child_index = None
            if any(child.humanoid_bone for child in node.children):
                # humanioid
                for i, child in enumerate(node.children):
                    if child.humanoid_bone:
                        if child.humanoid_bone in [
                                formats.HumanoidBones.hips,
                                formats.HumanoidBones.leftUpperLeg,
                                formats.HumanoidBones.rightUpperLeg,
                                formats.HumanoidBones.leftShoulder,
                                formats.HumanoidBones.rightShoulder,
                                formats.HumanoidBones.leftEye,
                                formats.HumanoidBones.rightEye,
                        ]:
                            continue
                        connect_child_index = i
                        break
            else:
                for i, child in enumerate(node.children):
                    if child.name in [
                            'J_Adj_L_FaceEyeSet', 'J_Adj_R_FaceEyeSet'
                    ]:
                        continue
                    # とりあえず
                    connect_child_index = i
                    break

            # select connect child
            for i, child in enumerate(node.children):
                self.traverse(child, node, i == connect_child_index)
        else:
            # stop recursive
            self.extend_tail(node)


def connect_bones(bones: Dict[pyscene.Node, bpy.types.EditBone]):

    nodes = bones.keys()
    roots = []
    for node in nodes:
        if not node.parent:
            roots.append(node)
        elif node.parent not in nodes:
            roots.append(node)

    connector = BoneConnector(bones)
    for root in roots:
        connector.traverse(root, None, False)


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

        self.obj_map: Dict[pyscene.Node, bpy.types.Object] = {}
        self.mesh_map: Dict[pyscene.SubmeshMesh, bpy.types.Mesh] = {}
        self.material_importer = MaterialImporter()
        self.skin_map: Dict[pyscene.Skin, bpy.types.Object] = {}

    def _setup_skinning(self, mesh_node: pyscene.Node) -> None:
        if not isinstance(mesh_node.mesh, pyscene.SubmeshMesh):
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

    def _create_bones(self, armature: bpy.types.Armature, m: mathutils.Matrix,
                      skin_node: pyscene.Node, skin: pyscene.Skin) -> None:
        '''
        ボーンを作る

        tail を決める

        * child が 0。親からまっすぐに伸ばす
        * child が ひとつ。それ
        * chidl が 2つ以上。どれか選べ
        '''
        # pass1: create and head postiion
        bones: Dict[pyscene.Node, bpy.types.EditBone] = {}
        for node in skin.joints:
            bl_object = self.obj_map[node]
            bl_bone = armature.edit_bones.new(node.name)
            # get armature local matrix
            world_to_local = m @ bl_object.matrix_world
            bl_bone.head = world_to_local @ mathutils.Vector((0, 0, 0))
            bl_bone.tail = bl_bone.head + mathutils.Vector((0, 0.1, 0))
            bones[node] = bl_bone

        # pass2: connect
        connect_bones(bones)

    def _create_armature(self, skin_node: pyscene.Node) -> bpy.types.Object:
        logger.debug(f'skin')
        # すべての Joints を子孫に持つノードを探す
        # while True:
        #     if node.contains(skin.joints):
        #         break
        if not skin_node.skin:
            raise Exception()
        skin = skin_node.skin
        if skin_node.parent:
            skin_node = skin_node.parent

        if skin_node.contains(skin.joints) and not skin_node.mesh:
            # replace node by armature
            bl_node = self.obj_map[skin_node]
            bl_node.name = 'tmp'

            bl_skin: bpy.types.Armature = bpy.data.armatures.new(skin.name)
            bl_obj = bpy.data.objects.new(skin.name, bl_skin)
            self.skin_map[skin] = bl_obj
            bl_obj.matrix_world = bl_node.matrix_world

            bl_obj.parent = bl_node.parent
            for bl_child in bl_node.children:
                bl_child.parent = bl_obj
            if bl_node.data:
                raise Exception()
            self.obj_map[skin_node] = bl_obj
            bpy.data.objects.remove(bl_node)
        else:
            # create new node
            bl_skin: bpy.types.Armature = bpy.data.armatures.new(skin.name)
            bl_obj = bpy.data.objects.new(skin.name, bl_skin)
            self.skin_map[skin] = bl_obj

        bl_obj.show_in_front = True
        self.collection.objects.link(bl_obj)

        # if skin.parent_space:
        #     bl_obj.parent = self.obj_map.get(skin.parent_space)

        self.context.view_layer.objects.active = bl_obj
        bl_obj.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # create bones
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        self._create_bones(bl_skin, bl_obj.matrix_world.inverted(), skin_node,
                           skin)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    def _create_humanoid(self, roots: List[pyscene.Node]) -> bpy.types.Object:
        '''
        Armature for Humanoid
        '''
        skins = [
            node.skin for root in roots for node in root.traverse()
            if node.skin
        ]
        # create new node
        bl_skin: bpy.types.Armature = bpy.data.armatures.new('Humanoid')
        # bl_skin.show_names = True
        bl_obj = bpy.data.objects.new('Humanoid', bl_skin)
        bl_obj.show_in_front = True
        self.collection.objects.link(bl_obj)

        # enter edit mode
        self.context.view_layer.objects.active = bl_obj
        bl_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        # 1st pass: create bones
        bones: Dict[pyscene.Node, bpy.types.EditBone] = {}
        for skin in skins:
            for node in skin.joints:
                if node in bones:
                    continue
                bl_object = self.obj_map[node]
                bl_bone = bl_skin.edit_bones.new(node.name)
                # get armature local matrix
                bl_bone.head = bl_object.matrix_world.translation
                bl_bone.tail = bl_bone.head + mathutils.Vector((0, 0.1, 0))
                bones[node] = bl_bone

        # 2nd pass: tail, connect
        connect_bones(bones)

        # exit edit mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        for skin in skins:
            self.skin_map[skin] = bl_obj

        return bl_obj

    def _get_or_create_mesh(self, mesh: pyscene.SubmeshMesh) -> bpy.types.Mesh:
        bl_mesh = self.mesh_map.get(mesh)
        if bl_mesh:
            return bl_mesh

        bl_mesh = bpy.data.meshes.new(mesh.name)
        self.mesh_map[mesh] = bl_mesh

        material_index_map: Dict[pyscene.UnlitMaterial, int] = {}
        material_index = 0
        for i, submesh in enumerate(mesh.submeshes):
            bl_material = self.material_importer.get_or_create_material(
                submesh.material)
            bl_mesh.materials.append(bl_material)
            material_index_map[submesh.material] = material_index
            material_index += 1

        # indices to material_index
        current = [0]

        def to_material_index(indices_index: int) -> int:
            submesh = mesh.submeshes[current[0]]
            indices_index -= submesh.offset
            if indices_index < 0:
                raise Exception()
            if indices_index >= submesh.vertex_count:
                current[0] += 1
                submesh = mesh.submeshes[current[0]]
            return material_index_map[submesh.material]

        bm = create_bmesh(mesh, to_material_index)
        bm.to_mesh(bl_mesh)

        # Shapekeys
        if len(bm.verts.layers.shape) != 0:
            # The only way I could find to create a shape key was to temporarily
            # parent mesh to an object and use obj.shape_key_add.
            tmp_ob = None
            try:
                tmp_ob = bpy.data.objects.new('##gltf-import:tmp-object##',
                                              bl_mesh)
                tmp_ob.shape_key_add(name='Basis')
                bl_mesh.shape_keys.name = bl_mesh.name
                for layer_name in bm.verts.layers.shape.keys():
                    tmp_ob.shape_key_add(name=layer_name)
                    key_block = bl_mesh.shape_keys.key_blocks[layer_name]
                    layer = bm.verts.layers.shape[layer_name]

                    for i, v in enumerate(bm.verts):
                        key_block.data[i].co = v[layer]
            finally:
                if tmp_ob:
                    bpy.data.objects.remove(tmp_ob)

        # *Very* important to not remove lnors here!
        # bl_mesh.validate(clean_customdata=False)
        bl_mesh.update()

        bl_mesh.create_normals_split()
        custom_normals = [v.normal for v in bm.verts]
        bl_mesh.normals_split_custom_set_from_vertices(custom_normals)
        bl_mesh.use_auto_smooth = True

        bm.free()  # free and prevent further access

        return bl_mesh

    def _create_object(self, node: pyscene.Node) -> None:
        '''
        Node から bpy.types.Object を作る
        '''
        # create object
        if isinstance(node.mesh, pyscene.SubmeshMesh):
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
        bl_obj.location = node.position.yup2zup()
        with tmp_mode(bl_obj, 'QUATERNION'):
            bl_obj.rotation_quaternion = mod_q(node.rotation)
        bl_obj.scale = mod_s(node.scale)

    def _create_tree(self,
                     node: pyscene.Node,
                     parent: Optional[pyscene.Node] = None):
        self._create_object(node)
        for child in node.children:
            self._create_tree(child, node)

    def _remove_empty(self, node: pyscene.Node):
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

        # remove empty
        bl_obj = self.obj_map[node]
        bpy.data.objects.remove(bl_obj, do_unlink=True)
        if node.parent:
            node.parent.children.remove(node)

    def execute(self, roots: List[pyscene.Node], is_vrm: bool):
        for root in roots:
            self._create_tree(root)

        if is_vrm:
            # Armature を ひとつの Humanoid にまとめる
            self._create_humanoid(roots)
        else:
            # skinning
            for root in roots:
                for node in root.traverse():
                    if node.skin:
                        self._create_armature(node)

        for n, o in self.obj_map.items():
            if o.type == 'MESH' and n.skin:
                self._setup_skinning(n)

        # remove empties
        for root in roots:
            self._remove_empty(root)
