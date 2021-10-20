from logging import getLogger

logger = getLogger(__name__)

import bpy
import mathutils
import bmesh
import math
from typing import List, Dict, Optional
from contextlib import contextmanager
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


EXCLUDE_HUMANOID_PARENT = [
    # formats.HumanoidBones.head
]

EXCLUDE_HUMANOID_CHILDREN = [
    # formats.HumanoidBones.hips,
    # formats.HumanoidBones.leftUpperLeg,
    # formats.HumanoidBones.rightUpperLeg,
    # formats.HumanoidBones.leftShoulder,
    # formats.HumanoidBones.rightShoulder,
    # formats.HumanoidBones.leftEye,
    # formats.HumanoidBones.rightEye,
    # #
    # formats.HumanoidBones.leftThumbProximal,
    # formats.HumanoidBones.leftIndexProximal,
    # formats.HumanoidBones.leftMiddleProximal,
    # formats.HumanoidBones.leftRingProximal,
    # formats.HumanoidBones.leftLittleProximal,
    # #
    # formats.HumanoidBones.rightThumbProximal,
    # formats.HumanoidBones.rightIndexProximal,
    # formats.HumanoidBones.rightMiddleProximal,
    # formats.HumanoidBones.rightRingProximal,
    # formats.HumanoidBones.rightLittleProximal,
]

EXCLUDE_OTHERS = ['J_Adj_L_FaceEyeSet', 'J_Adj_R_FaceEyeSet']


class BoneConnector:
    '''
    ボーンを適当に接続したり、しない場合でも tail を設定してやる

    tail を決める

    * child が 0。親からまっすぐに伸ばす
    * child が ひとつ。それ
    * child が 2つ以上。どれか選べ(同じざひょうのときは少しずらす。head と tail が同じボーンは消滅するので)
    '''
    def __init__(self, bones: Dict[gltf.Node, bpy.types.EditBone]):
        self.bones = bones

    def extend_tail(self, node: gltf.Node):
        '''
        親ボーンと同じ方向にtailを延ばす
        '''
        bl_bone = self.bones[node]
        if node.parent:
            try:
                bl_parent = self.bones[node.parent]
                tail_offset = (bl_bone.head - bl_parent.head)  # type: ignore
                bl_bone.tail = bl_bone.head + tail_offset
            except KeyError:
                print(f'{node}.parent not found')

    def connect_tail(self, node: gltf.Node, tail: gltf.Node):
        bl_bone = self.bones[node]
        bl_tail = self.bones[tail]
        bl_bone.tail = bl_tail.head
        bl_tail.parent = bl_bone
        bl_tail.use_connect = True

    def traverse(self, node: gltf.Node, parent: Optional[gltf.Node],
                 is_connect: bool):
        # connect
        if parent:
            # print(f'connect {parent} => {node}')
            bl_parent = self.bones[parent]
            bl_bone = self.bones.get(node)
            if not bl_bone:
                # not in skin
                return

            bl_bone.parent = bl_parent
            if is_connect:
                if bl_parent.head != bl_bone.head:
                    bl_parent.tail = bl_bone.head
                else:
                    bl_parent.tail = bl_bone.head + mathutils.Vector(
                        (0, 0, 1e-4))

                # if parent and (parent.humanoid_bone
                #                == formats.HumanoidBones.leftShoulder
                #                or parent.humanoid_bone
                #                == formats.HumanoidBones.rightShoulder):
                #     # https://blenderartists.org/t/rigify-error-generation-has-thrown-an-exception-but-theres-no-exception-message/1228840
                #     pass
                # else:
                if True:
                    bl_bone.use_connect = True

        if node.children:
            # recursive
            connect_child_index = None
            if node.humanoid_bone in EXCLUDE_HUMANOID_PARENT:
                pass
            elif any(child.humanoid_bone for child in node.children):
                # humanioid
                for i, child in enumerate(node.children):
                    if child.humanoid_bone:
                        if child.humanoid_bone in EXCLUDE_HUMANOID_CHILDREN:
                            continue
                        connect_child_index = i
                        break
            else:
                for i, child in enumerate(node.children):
                    if child.name in EXCLUDE_OTHERS:
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


def connect_bones(bones: Dict[gltf.Node, bpy.types.EditBone]):

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


MODE_MAP = {
    'OBJECT': 'OBJECT',
    'EDIT': 'EDIT',
    'EDIT_MESH': 'EDIT',
    'EDIT_ARMATURE': 'EDIT',
    'SCULPT': 'OBJECT',
    'POSE': 'POSE',
    'VERTEX_PAINT': 'OBJECT',
    'WEIGHT_PAINT': 'OBJECT',
    'PAINT_WEIGHT': 'OBJECT',
    'TEXTURE_PAINT': 'OBJECT',
}


@contextmanager
def disposable_mode(bl_obj: bpy.types.Object, mode='OBJECT'):
    '''
    モードを変更して元のモードに戻る
    '''
    bpy.context.view_layer.objects.active = bl_obj

    restore = MODE_MAP[bpy.context.mode]
    try:
        if restore != mode:
            bpy.ops.object.mode_set(mode=mode, toggle=False)
        yield None
    finally:
        if bpy.context.mode != restore:
            bpy.ops.object.mode_set(mode=restore, toggle=False)


def convert_obj(src: gltf.Coodinate, dst: gltf.Coodinate,
                bl_obj: bpy.types.Object):
    if dst == gltf.Coodinate.BLENDER_ROTATE:
        if src == gltf.Coodinate.VRM0:
            bl_obj.rotation_euler = (math.pi * 0.5, 0, math.pi)
        else:
            raise NotImplementedError()
    else:
        raise NotImplementedError()


def bl_traverse(bl_obj: bpy.types.Object, pred):
    pred(bl_obj)

    for child in bl_obj.children:
        bl_traverse(child, pred)


class Importer:
    def __init__(self, context: bpy.types.Context,
                 conversion: gltf.Conversion):
        self.collection = context.scene.collection
        self.conversion = conversion
        self.obj_map: Dict[gltf.Node, bpy.types.Object] = {}
        self.mesh_map: Dict[gltf.Mesh, bpy.types.Mesh] = {}
        self.mesh_obj_list: List[bpy.types.Object] = []
        self.matrix_map = {}
        self.skin_map: Dict[gltf.Skin, bpy.types.Object] = {}

    def _get_or_create_mesh(self, mesh: gltf.Mesh) -> bpy.types.Mesh:
        bl_mesh = self.mesh_map.get(mesh)
        if bl_mesh:
            return bl_mesh

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
        self.mesh_map[mesh] = bl_mesh

        bm.to_mesh(bl_mesh)
        bm.free()

        return bl_mesh

    def _create_object(self, node: gltf.Node) -> None:
        '''
        Node から bpy.types.Object を作る
        '''
        # create object
        if isinstance(node.mesh, gltf.Mesh):
            bl_mesh = self._get_or_create_mesh(node.mesh)
            bl_obj: bpy.types.Object = bpy.data.objects.new(node.name, bl_mesh)
        else:
            # empty
            bl_obj: bpy.types.Object = bpy.data.objects.new(node.name, None)
            bl_obj.empty_display_size = 0.1

        self.collection.objects.link(bl_obj)
        bl_obj.select_set(True)
        self.obj_map[node] = bl_obj
        # parent
        if node.parent:
            bl_obj.parent = self.obj_map.get(node.parent)

        # TRS
        bl_obj.location = node.translation
        # with tmp_mode(bl_obj, 'QUATERNION'):
        bl_obj.rotation_quaternion = node.rotation
        bl_obj.scale = node.scale

        self.matrix_map[node] = bl_obj.matrix_world
        return bl_obj

    def _create_tree(self,
                     node: gltf.Node,
                     parent: Optional[gltf.Node] = None,
                     level=0):
        indent = '  ' * level
        # print(f'{indent}{node.name}')
        bl_obj = self._create_object(node)
        for child in node.children:
            self._create_tree(child, node, level + 1)
        return bl_obj

    def _create_humanoid(self, roots: List[gltf.Node]) -> bpy.types.Object:
        '''
        Armature for Humanoid
        '''
        skins = [
            node.skin for root in roots for node in root.traverse()
            if node.skin
        ]
        # create new node
        bl_skin = bpy.data.armatures.new('Humanoid')
        bl_skin.use_mirror_x = True
        # bl_skin.show_names = True
        bl_skin.display_type = 'STICK'
        bl_obj = bpy.data.objects.new('Humanoid', bl_skin)
        bl_obj.show_in_front = True
        self.collection.objects.link(bl_obj)

        # enter edit mode
        bpy.context.view_layer.objects.active = bl_obj
        bl_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        # 1st pass: create bones
        bones: Dict[gltf.Node, bpy.types.EditBone] = {}
        for skin in skins:
            for node in skin.joints:
                if node in bones:
                    continue
                bl_object = self.obj_map.get(node)
                if not bl_object:
                    # maybe removed as empty leaf
                    continue
                bl_bone = bl_skin.edit_bones.new(node.name)
                # get armature local matrix
                bl_bone.head = bl_object.matrix_world.translation
                bl_bone.tail = bl_bone.head + mathutils.Vector((0, 0.1, 0))
                bones[node] = bl_bone

        # 2nd pass: tail, connect
        connect_bones(bones)

        humaniod_map: Dict[formats.HumanoidBones, gltf.Node] = {}
        for k, v in bones.items():
            if k.humanoid_bone:
                humaniod_map[k.humanoid_bone] = k

        # set bone group
        with disposable_mode(bl_obj, 'POSE'):
            bone_group = bl_obj.pose.bone_groups.new(name='humanoid')
            bone_group.color_set = 'THEME01'
            for node in humaniod_map.values():
                b = bl_obj.pose.bones[node.name]
                b.bone_group = bone_group
                # property
                b.pyimpex_humanoid_bone = node.humanoid_bone.name

        for skin in skins:
            self.skin_map[skin] = bl_obj

        # #
        # # set metarig
        # #
        # with disposable_mode(bl_obj, 'EDIT'):
        #     # add heel
        #     def create_heel(bl_armature: bpy.types.Armature, name: str,
        #                     bl_parent: bpy.types.EditBone, tail_offset):
        #         bl_heel_l = bl_armature.edit_bones.new(name)
        #         bl_heel_l.use_connect = False
        #         # print(bl_parent)
        #         bl_heel_l.parent = bl_parent
        #         y = 0.1
        #         bl_heel_l.head = (bl_parent.head.x, y, 0)
        #         bl_heel_l.tail = (bl_parent.head.x + tail_offset, y, 0)

        #     bl_armature = bl_obj.data
        #     if isinstance(bl_armature, bpy.types.Armature):
        #         left_foot_node = humaniod_map[formats.HumanoidBones.leftFoot]
        #         create_heel(bl_armature, 'heel.L',
        #                     bl_armature.edit_bones[left_foot_node.name], 0.1)
        #         right_foot_node = humaniod_map[formats.HumanoidBones.rightFoot]
        #         create_heel(bl_armature, 'heel.R',
        #                     bl_armature.edit_bones[right_foot_node.name], -0.1)

        # with disposable_mode(bl_obj, 'POSE'):
        #     for k, v in bones.items():
        #         if k.humanoid_bone:
        #             b = bl_obj.pose.bones[k.name]
        #             try:
        #                 rigify_type = METALIG_MAP.get(k.humanoid_bone)
        #                 if rigify_type:
        #                     b.rigify_type = rigify_type
        #                 else:
        #                     print(k.humanoid_bone)
        #             except Exception as ex:
        #                 print(ex)
        #                 break

        # text: bpy.types.Text = bpy.data.texts.new('bind_rigify.py')
        # text.from_string(BIND_RIGIFY)

        return bl_obj

    def load(self, loader: gltf.Loader):
        # create object for each node
        root_objs = []
        for root in loader.roots:
            bl_obj = self._create_tree(root)
            root_objs.append(bl_obj)

        # apply conversion
        empty = bpy.data.objects.new("empty", None)
        self.collection.objects.link(empty)
        for bl_obj in root_objs:
            bl_obj.parent = empty
        convert_obj(self.conversion.src, self.conversion.dst, empty)

        def apply(o: bpy.types.Object):
            o.select_set(True)
            bpy.ops.object.transform_apply(location=False,
                                           rotation=True,
                                           scale=False)
            o.select_set(False)

        bpy.ops.object.select_all(action='DESELECT')
        bl_traverse(empty, apply)
        empty.select_set(True)
        bpy.ops.object.delete(use_global=False)

        if loader.vrm:
            # single skin humanoid model
            pass
        else:
            # non humanoid generic scene
            pass

        bl_humanoid_obj = self._create_humanoid(loader.roots)
        # Mesh を Armature の子にする
        for bl_obj in self.mesh_obj_list:
            if isinstance(bl_obj.data, bpy.types.Mesh):
                bl_obj.parent = bl_humanoid_obj
            else:
                bpy.data.objects.remove(bl_obj, do_unlink=True)
