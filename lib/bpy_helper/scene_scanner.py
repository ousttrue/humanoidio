from typing import List, Optional, Iterator, Dict, Any
import bpy, mathutils
from .. import bpy_helper
from ..pyscene.facemesh import FaceMesh
from ..pyscene.node import Node
from ..formats.vrm0x import HumanoidBones


class Vrm:
    def __init__(self):
        self.title = ''
        self.author = ''
        self.version = '1'


class Scanner:
    def __init__(self) -> None:
        self._nodes: List[Node] = []
        self._node_map: Dict[bpy.types.Object, Node] = {}
        self.meshes: List[FaceMesh] = []
        self.materials: List[bpy.types.Material] = []
        self.skin_map: Dict[bpy.types.Object, Node] = {}
        self.vrm = Vrm()

    def _add_node(self, obj: Any, node: Node):
        self._nodes.append(node)
        self._node_map[obj] = node

    def get_root_nodes(self) -> Iterator[Node]:
        for node in self._nodes:
            if not node.parent:
                yield node

    def remove_node(self, node: Node):
        # _node_map
        keys = []
        for k, v in self._node_map.items():
            if v == node:
                keys.append(k)
        for k in keys:
            del self._node_map[k]

        # _nodes
        self._nodes.remove(node)

        # children
        if node.parent:
            node.parent.remove_child(node)

    def remove_empty_leaf_nodes(self) -> bool:
        bones: List[Node] = []
        for skin in self.skin_map.values():
            for bone in skin.traverse():
                if bone not in bones:
                    bones.append(bone)

        def is_empty_leaf(node: Node) -> bool:
            if node.humanoid_bone:
                return False
            if node.children:
                return False
            if node.mesh:
                return False
            if node in bones:
                return False
            return True

        remove_list = []
        for root in self.get_root_nodes():
            for node in root.traverse():
                if is_empty_leaf(node):
                    remove_list.append(node)

        if not remove_list:
            return False

        for remove in remove_list:
            self.remove_node(remove)

        return True

    def add_mesh_node(self):
        mesh_node = Node('Mesh')
        for node in self._nodes:
            if node.mesh:
                mesh_node.add_child(node)
        self._nodes.append(mesh_node)

    def _export_bone(self, parent: Node, matrix_world: mathutils.Matrix,
                     bone: bpy.types.Bone) -> Node:
        armature_local_head_position = bone.head_local
        node = Node(bone.name, armature_local_head_position)
        if hasattr(bone, 'humanoid_bone'):
            humanoid_bone = bone.humanoid_bone
            if humanoid_bone:
                try:
                    parsed = HumanoidBones[humanoid_bone]
                    if parsed != HumanoidBones.unknown:
                        node.humanoid_bone = parsed
                except Exception:
                    # unknown
                    pass

        parent.add_child(node)
        self._add_node(bone, node)

        for child in bone.children:
            self._export_bone(node, matrix_world, child)

        return node

    def _get_or_create_skin(self, armature_object: bpy.types.Object) -> Node:
        if armature_object in self.skin_map:
            return self.skin_map[armature_object]

        bpy.context.view_layer.objects.active = armature_object
        with bpy_helper.disposable_mode('POSE'):

            armature_node = self._get_or_create_node(armature_object)
            self.skin_map[armature_object] = armature_node

            armature = armature_object.data
            for b in armature.bones:
                if not b.parent:
                    # root bone
                    self._export_bone(armature_node,
                                      armature_object.matrix_world, b)

        # get vrm meta
        self.vrm.version = armature_object.get('vrm_version')
        self.vrm.title = armature_object.get('vrm_title')
        self.vrm.author = armature_object.get('vrm_author')
        # self.vrm.contactInformation = armature_object['vrm_contactInformation']
        # self.vrm.reference = armature_object['vrm_reference']

        return armature_node

    def _export_mesh(self, o: bpy.types.Object, mesh: bpy.types.Mesh,
                     node: Node) -> FaceMesh:
        # copy
        new_obj = bpy_helper.clone_and_apply_transform(o)
        with bpy_helper.disposable(new_obj):
            new_mesh: bpy.types.Mesh = new_obj.data

            # clear shape key
            new_obj.shape_key_clear()
            # otherwise
            # Error: Modifier cannot be applied to a mesh with shape keys

            # first create skin
            for m in new_obj.modifiers:
                if m.type == 'ARMATURE':
                    node.skin = self._get_or_create_skin(m.object)
                    break

            # apply modifiers
            bpy_helper.apply_modifiers(new_obj)

            # メッシュの三角形化
            if bpy.app.version[1] > 80:
                new_mesh.calc_loop_triangles()
                new_mesh.update()
            else:
                new_mesh.update(calc_loop_triangles=True)
            triangles = [i for i in new_mesh.loop_triangles]

            def get_texture_layer(layers):
                for l in layers:
                    if l.active:
                        return l

            uv_texture_layer = get_texture_layer(new_mesh.uv_layers)

            # vertices
            bone_names = [b.name
                          for b in node.skin.traverse()] if node.skin else []
            store = FaceMesh(o.name, new_mesh.vertices, new_mesh.materials,
                             o.vertex_groups, bone_names)
            # triangles
            for i, triangle in enumerate(triangles):
                store.add_triangle(triangle, uv_texture_layer)

            # shapekey
            if o.data.shape_keys:
                for i, shape in enumerate(o.data.shape_keys.key_blocks):
                    if shape.name == 'Basis':
                        continue

                    #
                    # copy and apply shapekey
                    #
                    vertices = self._export_shapekey(o, i, shape)
                    # store.add_morph(shape.name, vertices)

            return store

    def _export_shapekey(self, o: bpy.types.Object, i: int,
                         shape: bpy.types.ShapeKey):
        # copy
        new_obj = bpy_helper.clone_and_apply_transform(o)
        with bpy_helper.disposable(new_obj):
            new_mesh: bpy.types.Mesh = new_obj.data

            # apply shape key
            bpy_helper.remove_shapekey_except(new_obj, i)
            new_obj.shape_key_clear()

            # apply modifiers
            bpy_helper.apply_modifiers(new_obj)

            # メッシュの三角形化
            if bpy.app.version[1] > 80:
                new_mesh.calc_loop_triangles()
                new_mesh.update()
            else:
                new_mesh.update(calc_loop_triangles=True)

            # POSITIONSを得る
            return [v for v in new_mesh.vertices]

    def _get_or_create_node(self, o: bpy.types.Object) -> Node:
        if o in self._node_map:
            return self._node_map[o]

        # location = o.location
        # if o.parent:
        #     location -= o.parent.location
        node = Node(o.name, mathutils.Vector((0, 0, 0)))
        self._add_node(o, node)
        return node

    def _export_object(self,
                       o: bpy.types.Object,
                       parent: Optional[Node] = None) -> Node:
        '''
        scan Node recursive
        '''
        node = self._get_or_create_node(o)
        if parent:
            parent.add_child(node)

        for slot in o.material_slots:
            if slot and slot not in self.materials:
                self.materials.append(slot.material)

        if o.type == 'MESH':
            if not o.hide_viewport:
                mesh = self._export_mesh(o, o.data, node)
                self.meshes.append(mesh)
                node.mesh = mesh

        for child in o.children:
            self._export_object(child, node)

        return node

    def scan(self, roots: List[bpy.types.Object]) -> None:
        for root in roots:
            self._export_object(root)

    def get_skin_for_store(self, store: FaceMesh) -> Optional[Node]:
        for node in self._nodes:
            if node.mesh == store:
                return node.skin
        return None
