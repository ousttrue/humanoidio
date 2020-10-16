import json
from typing import Optional, List, Iterable
from contextlib import contextmanager

import bpy
import mathutils  # pylint: disable=E0401

from scene_translator.formats import gltf
from . import import_manager

from logging import getLogger  # pylint: disable=C0411
logger = getLogger(__name__)


@contextmanager
def tmp_mode(obj, tmp: str):
    mode = obj.rotation_mode
    obj.rotation_mode = tmp
    try:
        yield
    finally:
        obj.rotation_mode = mode


class Node:
    def __init__(self, index: int, gltf_node: gltf.Node) -> None:
        self.index = index
        self.gltf_node = gltf_node
        self.parent: Optional[Node] = None
        self.children: List[Node] = []
        self.blender_object: bpy.types.Object = None
        self.blender_armature: bpy.types.Object = None
        self.blender_bone: bpy.types.Bone = None
        self.bone_name: str = ''

        self.name = self.gltf_node.name
        if not self.name:
            self.name = '_%03d' % self.index

    def __str__(self) -> str:
        return f'{self.index}'

    def __repr__(self) -> str:
        return f'<{self.index}: {self.blender_object}>'

    def traverse(self) -> Iterable['Node']:
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x

    def get_ancestors(self) -> Iterable['Node']:
        yield self
        if self.parent:
            for x in self.parent.get_ancestors():
                yield x

    def create_object(self, collection: bpy.types.Collection,
                      manager: import_manager.ImportManager) -> None:
        # create object
        if self.gltf_node.mesh != -1:
            self.blender_object = bpy.data.objects.new(
                self.name, manager.meshes[self.gltf_node.mesh][0])
        else:
            # empty
            self.blender_object = bpy.data.objects.new(self.name, None)
            self.blender_object.empty_display_size = 0.1
            # self.blender_object.empty_draw_type = 'PLAIN_AXES'
        collection.objects.link(self.blender_object)
        self.blender_object.select_set(True)

        # self.blender_object['js'] = json.dumps(self.gltf_node.js, indent=2)

        # parent
        if self.parent:
            self.blender_object.parent = self.parent.blender_object

        if self.gltf_node.translation:
            self.blender_object.location = manager.mod_v(
                self.gltf_node.translation)

        if self.gltf_node.rotation:
            r = self.gltf_node.rotation
            q = mathutils.Quaternion((r[3], r[0], r[1], r[2]))
            with tmp_mode(self.blender_object, 'QUATERNION'):
                self.blender_object.rotation_quaternion = manager.mod_q(q)

        if self.gltf_node.scale:
            s = self.gltf_node.scale
            self.blender_object.scale = (s[0], s[2], s[1])

        if self.gltf_node.matrix:
            m = self.gltf_node.matrix
            matrix = mathutils.Matrix(
                ((m[0], m[4], m[8], m[12]), (m[1], m[5], m[9], m[13]),
                 (m[2], m[6], m[10], m[14]), (m[3], m[7], m[11], m[15])))
            t, q, s = matrix.decompose()
            self.blender_object.location = manager.mod_v(t)
            with tmp_mode(self.blender_object, 'QUATERNION'):
                self.blender_object.rotation_quaternion = manager.mod_q(q)
            self.blender_object.scale = (s[0], s[2], s[1])

        for child in self.children:
            child.create_object(collection, manager)

    # create armature
    def create_armature(self, context, collection, view_layer,
                        skin: gltf.Skin) -> bpy.types.Object:
        skin_name = skin.name

        armature = bpy.data.armatures.new(skin_name)
        self.blender_armature = bpy.data.objects.new(skin_name, armature)
        collection.objects.link(self.blender_armature)
        self.blender_armature.show_in_front = True
        if not self.blender_object:
            raise Exception('no blender_object: %s' % self)

        self.blender_armature.parent = self.blender_object.parent

        # select
        self.blender_armature.select_set("SELECT")
        view_layer.objects.active = self.blender_armature
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # set identity matrix_world to armature
        m = mathutils.Matrix()
        m.identity()
        self.blender_armature.matrix_world = m
        context.scene.update()  # recalc matrix_world

        # edit mode
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        self.create_bone(skin, armature, None, False)

    def create_bone(self, skin: gltf.Skin, armature: bpy.types.Armature,
                    parent_bone: bpy.types.Bone, is_connect: bool) -> None:

        self.blender_bone = armature.edit_bones.new(self.name)
        self.bone_name = self.blender_bone.name
        self.blender_bone.parent = parent_bone
        if is_connect:
            self.blender_bone.use_connect = True

        object_pos = self.blender_object.matrix_world.to_translation()
        self.blender_bone.head = object_pos

        if not is_connect:
            if parent_bone and parent_bone.tail == (0, 0, 0):
                tail_offset = (self.blender_bone.head -
                               parent_bone.head).normalized() * 0.1
                parent_bone.tail = parent_bone.head + tail_offset

        if not self.children:
            if parent_bone:
                self.blender_bone.tail = self.blender_bone.head + \
                    (self.blender_bone.head - parent_bone.head)
        else:

            def get_child_is_connect(child_pos) -> bool:
                if len(self.children) == 1:
                    return True

                if abs(child_pos.x) < 0.001:
                    return True

                return False

            if parent_bone:
                child_is_connect = 0
                for i, child in enumerate(self.children):
                    if get_child_is_connect(child.blender_object.matrix_world.
                                            to_translation()):
                        child_is_connect = i
            else:
                child_is_connect = -1

            for i, child in enumerate(self.children):
                child.create_bone(skin, armature, self.blender_bone,
                                  i == child_is_connect)
