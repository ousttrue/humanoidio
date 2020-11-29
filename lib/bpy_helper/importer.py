from logging import getLogger
from math import exp

from bpy.types import Armature
logger = getLogger(__name__)
from contextlib import contextmanager
from typing import List, Optional, Dict, Set
import bpy, mathutils
from .. import pyscene
from .materials import MaterialImporter
from .mesh_importer import create_bmesh
from .bone_connector import connect_bones
from . import custom_rna
from . import utils
from .. import formats

BIND_RIGIFY = '''
# object mode で 生成した rig をアクティブにして実行する
print()
print('### start ###')

import bpy

armature_obj = bpy.context.view_layer.objects.active
armature = armature_obj.data
print(armature)

# edit_bones にアクセスするのに必要
bpy.ops.object.mode_set(mode='EDIT')

# DEF- を消す
defs = [b for b in armature.edit_bones if b.name.startswith('DEF-')]
print(defs)
for b in defs:
    armature.edit_bones.remove(b)

# ORG- の deform を有効にする
for b in armature.edit_bones:
    if b.name.startswith('ORG-'):
        b.use_deform = True

bpy.ops.object.mode_set(mode='OBJECT')

# シーンのオブジェクトを列挙
for o in bpy.data.objects:
    # armature を生成した rig に設定
    for m in  o.modifiers:
        if m.type != 'ARMATURE':
            continue            
        m.object = armature_obj

    # vertex group の名前を変える
    for vg in o.vertex_groups:
        if vg.name.startswith('ORG-'):
            continue
        vg.name = 'ORG-' + vg.name
'''


@contextmanager
def tmp_mode(obj, tmp: str):
    mode = obj.rotation_mode
    obj.rotation_mode = tmp
    try:
        yield
    finally:
        obj.rotation_mode = mode


METALIG_MAP = {
    formats.HumanoidBones.hips:
    'spines.basic_spine',
    formats.HumanoidBones.neck:
    'spines.super_head',
    formats.HumanoidBones.leftUpperLeg:
    'limbs.leg',
    formats.HumanoidBones.rightUpperLeg:
    'limbs.leg',
    # left arm
    formats.HumanoidBones.leftShoulder:
    'basic.super_copy',
    formats.HumanoidBones.leftUpperArm:
    'limbs.arm',
    # formats.HumanoidBones.leftHand: 'limbs.super_palm',
    formats.HumanoidBones.leftThumbProximal:
    'limbs.super_finger',
    formats.HumanoidBones.leftIndexProximal:
    'limbs.super_finger',
    formats.HumanoidBones.leftMiddleProximal:
    'limbs.super_finger',
    formats.HumanoidBones.leftRingProximal:
    'limbs.super_finger',
    formats.HumanoidBones.leftLittleProximal:
    'limbs.super_finger',

    # right arm
    formats.HumanoidBones.rightShoulder:
    'basic.super_copy',
    formats.HumanoidBones.rightUpperArm:
    'limbs.arm',
    # formats.HumanoidBones.rightHand: 'limbs.super_palm',
    formats.HumanoidBones.rightThumbProximal:
    'limbs.super_finger',
    formats.HumanoidBones.rightIndexProximal:
    'limbs.super_finger',
    formats.HumanoidBones.rightMiddleProximal:
    'limbs.super_finger',
    formats.HumanoidBones.rightRingProximal:
    'limbs.super_finger',
    formats.HumanoidBones.rightLittleProximal:
    'limbs.super_finger',
}


class Importer:
    '''
    bpy.types.Object, Mesh, Material, Texture を作成する
    '''
    def __init__(self, collection: bpy.types.Collection,
                 vrm: Optional[pyscene.Vrm]):
        self.collection = collection
        self.obj_map: Dict[pyscene.Node, bpy.types.Object] = {}
        self.mesh_map: Dict[pyscene.SubmeshMesh, bpy.types.Mesh] = {}
        self.material_importer = MaterialImporter()
        self.skin_map: Dict[pyscene.Skin, bpy.types.Object] = {}
        self.mesh_obj_list: List[bpy.types.Object] = []

        # coordinates
        self.vrm = vrm
        if self.vrm:
            self.yup2zup = lambda f3: ((-f3.x, f3.z, f3.y))
        else:
            self.yup2zup = lambda f3: ((f3.x, -f3.z, f3.y))

        def mod_q(_q):
            q = mathutils.Quaternion((_q.w, _q.x, _q.y, _q.z))
            return mathutils.Quaternion(self.yup2zup(q.axis), q.angle)

        self.yup2zup_q = mod_q
        self.yup2zup_s = lambda f3: (f3.x, f3.z, f3.y)

    def _setup_skinning(self, mesh_node: pyscene.Node) -> None:
        if not isinstance(mesh_node.mesh, pyscene.SubmeshMesh):
            return
        if not mesh_node.skin:
            return

        skin = mesh_node.skin
        bone_names = [joint.name for joint in skin.joints]
        bl_object = self.obj_map[mesh_node]

        idx_already_done: Set[int] = set()

        attributes = mesh_node.mesh.attributes

        # each face
        if isinstance(bl_object.data, bpy.types.Mesh):
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
                                try:
                                    group = bl_object.vertex_groups[bone_name]
                                except KeyError:
                                    group = bl_object.vertex_groups.new(
                                        name=bone_name)
                                group.add([vert_idx], weight_val, 'REPLACE')
                        cpt += 1

        modifier = bl_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = self.skin_map[skin]

    def _create_bones(self, armature: bpy.types.Armature, m: mathutils.Matrix,
                      skin_node: pyscene.Node, skin: pyscene.Skin) -> None:
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

        bpy.context.view_layer.objects.active = bl_obj
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
        bones: Dict[pyscene.Node, bpy.types.EditBone] = {}
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

        humaniod_map: Dict[formats.HumanoidBones, pyscene.Node] = {}
        for k, v in bones.items():
            if k.humanoid_bone:
                humaniod_map[k.humanoid_bone] = k

        # set bone group
        with utils.disposable_mode(bl_obj, 'POSE'):
            bone_group = bl_obj.pose.bone_groups.new(name='humanoid')
            bone_group.color_set = 'THEME01'
            for node in humaniod_map.values():
                b = bl_obj.pose.bones[node.name]
                b.bone_group = bone_group
                # property
                b.pyimpex_humanoid_bone = node.humanoid_bone.name

        for skin in skins:
            self.skin_map[skin] = bl_obj

        #
        # set metarig
        #
        with utils.disposable_mode(bl_obj, 'EDIT'):
            # add heel
            def create_heel(bl_armature: bpy.types.Armature, name: str,
                            bl_parent: bpy.types.EditBone, tail_offset):
                bl_heel_l = bl_armature.edit_bones.new(name)
                bl_heel_l.use_connect = False
                # print(bl_parent)
                bl_heel_l.parent = bl_parent
                y = 0.1
                bl_heel_l.head = (bl_parent.head.x, y, 0)
                bl_heel_l.tail = (bl_parent.head.x + tail_offset, y, 0)

            bl_armature = bl_obj.data
            if isinstance(bl_armature, bpy.types.Armature):
                left_foot_node = humaniod_map[formats.HumanoidBones.leftFoot]
                create_heel(bl_armature, 'heel.L',
                            bl_armature.edit_bones[left_foot_node.name], 0.1)
                right_foot_node = humaniod_map[formats.HumanoidBones.rightFoot]
                create_heel(bl_armature, 'heel.R',
                            bl_armature.edit_bones[right_foot_node.name], -0.1)
        with utils.disposable_mode(bl_obj, 'POSE'):
            for k, v in bones.items():
                if k.humanoid_bone:
                    b = bl_obj.pose.bones[k.name]
                    try:
                        rigify_type = METALIG_MAP.get(k.humanoid_bone)
                        if rigify_type:
                            b.rigify_type = rigify_type
                        else:
                            print(k.humanoid_bone)
                    except Exception as ex:
                        print(ex)
                        break

        text: bpy.types.Text = bpy.data.texts.new('bind_rigify.py')
        text.from_string(BIND_RIGIFY)

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
                if current[0] >= len(mesh.submeshes):
                    a = 0
                submesh = mesh.submeshes[current[0]]
            return material_index_map[submesh.material]

        bm = create_bmesh(mesh, to_material_index, self.yup2zup)
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

        self.collection.objects.link(bl_obj)
        bl_obj.select_set(True)
        self.obj_map[node] = bl_obj

        # parent
        if node.parent:
            bl_obj.parent = self.obj_map.get(node.parent)

        # TRS
        bl_obj.location = self.yup2zup(node.position)
        with tmp_mode(bl_obj, 'QUATERNION'):
            bl_obj.rotation_quaternion = self.yup2zup_q(node.rotation)
        bl_obj.scale = self.yup2zup_s(node.scale)

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

    def _get_shape_key(self, morph_bind):
        bl_obj = self.obj_map[morph_bind.node]
        if not bl_obj.data:
            raise Exception(f'{morph_bind.node}.data is None')
        mesh = bl_obj.data
        if not isinstance(mesh, bpy.types.Mesh):
            raise Exception(f'{morph_bind.node}.data is not bpy.types.Mesh')

        # bpy.context.view_layer.objects.active = bl_obj
        return mesh.shape_keys.key_blocks[morph_bind.name]

    def _load_expressions(self, bl_obj: bpy.types.Object,
                          expressions: List[pyscene.VrmExpression]):

        with utils.disposable_mode(bl_obj, 'OBJECT'):
            for i, e in enumerate(expressions):
                expression: custom_rna.PYIMPEX_Expression = bl_obj.pyimpex_expressions.add(
                )
                expression.preset = e.preset.value
                expression.name = e.name

        for i, e in enumerate(expressions):
            for morph_bind in e.morph_bindings:
                shape_key = self._get_shape_key(morph_bind)

                d: bpy.types.FCurve = shape_key.driver_add('value')
                var = d.driver.variables.new()
                var.name = 'var'
                var.type = 'SINGLE_PROP'
                t = var.targets[0]
                t.id = bl_obj
                t.data_path = f'pyimpex_expressions[{i}].weight'
                d.driver.type = 'SCRIPTED'
                d.driver.expression = "var"

    def _load_expression_bone_driverse(self,
                                       bl_humanoid_obj: bpy.types.Object):

        # expression driver
        armature = bl_humanoid_obj.data
        if not isinstance(armature, bpy.types.Armature):
            raise Exception()

        with utils.disposable_mode(bl_humanoid_obj, 'EDIT'):
            x = 0.2
            y = 0
            z = 1.5
            for expression in self.vrm.expressions:
                bl_bone = armature.edit_bones.new(str(expression))

                bl_bone.head = (x, y, z)
                bl_bone.tail = (x, y + 0.1, z)
                z += 0.02

        # morph
        for expression in self.vrm.expressions:
            for i, morph_bind in enumerate(expression.morph_bindings):
                # create driver
                bl_obj = self.obj_map[morph_bind.node]
                mesh = bl_obj.data
                if not isinstance(mesh, bpy.types.Mesh):
                    raise Exception()

                bpy.context.view_layer.objects.active = bl_obj

                shape_key = mesh.shape_keys.key_blocks[morph_bind.name]

                #
                # https://sourcecodequery.com/example-method/bpy.ops.object.text_add
                #
                d: bpy.types.FCurve = shape_key.driver_add('value')
                var = d.driver.variables.new()
                var.name = 'var'
                var.type = 'TRANSFORMS'
                t = var.targets[0]
                # t.id_type = 'ARMATURE'
                # t.id = bl_humanoid_obj.data
                t.id = bl_humanoid_obj
                t.bone_target = str(expression)
                t.transform_space = 'LOCAL_SPACE'
                t.transform_type = 'LOC_X'
                d.driver.type = 'SCRIPTED'
                d.driver.expression = "var/0.1"

    def execute(self, roots: List[pyscene.Node]):
        for root in roots:
            self._create_tree(root)

        bl_humanoid_obj = None
        if self.vrm:
            # Armature を ひとつの Humanoid にまとめる
            bl_humanoid_obj = self._create_humanoid(roots)

            # Mesh を Armature の子にする
            for bl_obj in self.mesh_obj_list:
                if isinstance(bl_obj.data, bpy.types.Mesh):
                    bl_obj.parent = bl_humanoid_obj
                else:
                    bpy.data.objects.remove(bl_obj, do_unlink=True)

            # プロパティロード
            self._load_expressions(bl_humanoid_obj, self.vrm.expressions)
        else:
            # skinning
            for root in roots:
                for bl_obj in root.traverse():
                    if bl_obj.skin:
                        self._create_armature(bl_obj)

        for n, o in self.obj_map.items():
            if o.type == 'MESH' and n.skin:
                self._setup_skinning(n)

        # remove empties
        for root in roots:
            self._remove_empty(root)

        if self.vrm and bl_humanoid_obj:
            # reparent vrm mesh
            for bl_obj in self.collection.objects:
                if isinstance(bl_obj.data, bpy.types.Mesh):
                    bl_obj.parent = bl_humanoid_obj
                    # bl_obj.location = (0, 0, 0) # without BindMatcies ?
            for bl_obj in self.collection.objects:
                if not bl_obj.data and not bl_obj.parent and not bl_obj.children:
                    bpy.data.objects.remove(bl_obj, do_unlink=True)

        utils.enter_mode('OBJECT')
        for bl_obj in self.collection.objects:
            bl_obj.select_set(False)
