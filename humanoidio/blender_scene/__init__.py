from logging import getLogger

logger = getLogger(__name__)

import bpy
import bmesh
from typing import List
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


class Importer:
    def __init__(self, context: bpy.types.Context):
        self.collection = context.scene.collection

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
        bones: Dict[pyscene.Node, bpy.types.EditBone] = {}
        for skin in skins:
            for node in skin.joints:
                if node in bones:
                    continue
                bl_object = self.import_map.obj.get(node)
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
            self.import_map.skin[skin] = bl_obj

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

    def _load_mesh(self, mesh: gltf.Mesh):
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
        bl_obj = bpy.data.objects.new(name, bl_mesh)
        # Add the object into the scene.
        bpy.context.scene.collection.objects.link(bl_obj)

        bm.to_mesh(bl_mesh)
        bm.free()

    def load(self, loader: gltf.Loader):
        # self._create_humanoid(loader.roots)

        for mesh in loader.meshes:
            self._load_mesh(mesh)
