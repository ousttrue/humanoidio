from logging import getLogger
logger = getLogger(__name__)
from typing import List, Optional, Iterator, Dict, Any, Sequence
import bpy, mathutils
from .. import bpy_helper
from .. import pyscene
from .material_exporter import MaterialExporter


class Vrm:
    def __init__(self):
        self.title = ''
        self.author = ''
        self.version = '1'


class Exporter:
    def __init__(self) -> None:
        self.nodes: List[pyscene.Node] = []
        self.meshes: List[pyscene.FaceMesh] = []
        self._node_map: Dict[bpy.types.Object, pyscene.Node] = {}
        self._skin_map: Dict[bpy.types.Object, pyscene.Skin] = {}
        self.vrm = Vrm()
        self.material_exporter = MaterialExporter()

    def _add_node(self, obj: Any, node: pyscene.Node):
        self.nodes.append(node)
        self._node_map[obj] = node

    def _get_root_nodes(self) -> Iterator[pyscene.Node]:
        for node in self.nodes:
            if not node.parent:
                yield node

    def remove_node(self, node: pyscene.Node):
        # _node_map
        keys = []
        for k, v in self._node_map.items():
            if v == node:
                keys.append(k)
        for k in keys:
            del self._node_map[k]

        # _nodes
        self.nodes.remove(node)

        # children
        if node.parent:
            node.parent.remove_child(node)

    def _get_node_for_skin(self, skin: pyscene.Skin) -> Optional[pyscene.Node]:
        for node in self.nodes:
            if node.skin == skin:
                return node

    def remove_empty_leaf_nodes(self) -> bool:
        bones: List[pyscene.Node] = []
        for skin in self._skin_map.values():
            skin_node = self._get_node_for_skin(skin)
            if not skin_node:
                raise Exception()
            for bone in skin_node.traverse():
                if bone not in bones:
                    bones.append(bone)

        def is_empty_leaf(node: pyscene.Node) -> bool:
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
        for root in self._get_root_nodes():
            for node in root.traverse():
                if is_empty_leaf(node):
                    remove_list.append(node)

        if not remove_list:
            return False

        for remove in remove_list:
            self.remove_node(remove)

        return True

    # def _mesh_node_under_empty(self):
    #     mesh_node = pyscene.Node('Mesh')
    #     for node in self.nodes:
    #         if node.mesh:
    #             mesh_node.add_child(node)
    #     self.nodes.append(mesh_node)

    def _export_bone(self, parent: pyscene.Node,
                     matrix_world: mathutils.Matrix,
                     bone: bpy.types.Bone) -> pyscene.Node:
        armature_local_head_position = bone.head_local
        node = pyscene.Node(bone.name)
        node.position = armature_local_head_position
        # if hasattr(bone, 'humanoid_bone'):
        #     humanoid_bone = bone.humanoid_bone
        #     if humanoid_bone:
        #         try:
        #             parsed = HumanoidBones[humanoid_bone]
        #             if parsed != HumanoidBones.unknown:
        #                 node.humanoid_bone = parsed
        #         except Exception:
        #             # unknown
        #             pass

        parent.add_child(node)
        self._add_node(bone, node)

        for child in bone.children:
            self._export_bone(node, matrix_world, child)

        return node

    def _get_or_create_skin(self,
                            armature_object: bpy.types.Object) -> pyscene.Skin:
        if armature_object in self._skin_map:
            return self._skin_map[armature_object]

        bpy.context.view_layer.objects.active = armature_object
        with bpy_helper.disposable_mode('POSE'):

            armature_node = self._get_or_create_node(armature_object)
            self._skin_map[armature_object] = armature_node

            armature = armature_object.data
            for b in armature.bones:
                if not b.parent:
                    # root bone
                    self._export_bone(armature_node,
                                      armature_object.matrix_world, b)

        return armature_node

    def _export_mesh(self, o: bpy.types.Object, mesh: bpy.types.Mesh,
                     node: pyscene.Node) -> pyscene.FaceMesh:
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

            materials = [
                self.material_exporter.get_or_create_material(material)
                for material in new_mesh.materials
            ]

            # vertices
            # bone_names = [b.name
            #               for b in node.skin.traverse()] if node.skin else []
            facemesh = pyscene.FaceMesh(o.data.name, new_mesh.vertices,
                                        materials, o.vertex_groups, [])
            # triangles
            uv_texture_layer = get_texture_layer(new_mesh.uv_layers)
            for i, triangle in enumerate(triangles):
                facemesh.add_triangle(triangle, uv_texture_layer)

            # shapekey
            if o.data.shape_keys:
                for i, shape in enumerate(o.data.shape_keys.key_blocks):
                    if shape.name == 'Basis':
                        continue

                    #
                    # copy and apply shapekey
                    #
                    vertices = self._export_shapekey(o, i, shape)
                    facemesh.add_morph(shape.name, vertices)

            return facemesh

    def _export_shapekey(
            self, o: bpy.types.Object, i: int,
            shape: bpy.types.ShapeKey) -> Sequence[bpy.types.MeshVertex]:
        logger.debug(f'{i}: {shape}')

        # TODO: modifier

        # # copy
        # new_obj = bpy_helper.clone_and_apply_transform(o)
        # with bpy_helper.disposable(new_obj):
        #     new_mesh: bpy.types.Mesh = new_obj.data

        #     # apply shape key
        #     bpy_helper.remove_shapekey_except(new_obj, i)
        #     new_obj.shape_key_clear()

        #     # apply modifiers
        #     bpy_helper.apply_modifiers(new_obj)

        #     # メッシュの三角形化
        #     if bpy.app.version[1] > 80:
        #         new_mesh.calc_loop_triangles()
        #         new_mesh.update()
        #     else:
        #         new_mesh.update(calc_loop_triangles=True)

        #     # POSITIONSを得る
        #     return [v for v in new_mesh.vertices]

        return shape.data

    def _get_or_create_node(self, o: bpy.types.Object) -> pyscene.Node:
        if o in self._node_map:
            return self._node_map[o]

        # location = o.location
        # if o.parent:
        #     location -= o.parent.location
        node = pyscene.Node(o.name)
        self._add_node(o, node)
        return node

    def _export_object(self,
                       o: bpy.types.Object,
                       parent: Optional[pyscene.Node] = None) -> pyscene.Node:
        '''
        scan Node recursive
        '''
        node = self._get_or_create_node(o)
        if parent:
            parent.add_child(node)

        # for slot in o.material_slots:
        #     if slot and slot not in self.material_exporter.materials:
        #         self.materials.append(slot.material)

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

        # self._mesh_node_under_empty()
        while True:
            if not self.remove_empty_leaf_nodes():
                break

        # # get vrm meta
        # self.vrm.version = armature_object.get('vrm_version')
        # self.vrm.title = armature_object.get('vrm_title')
        # self.vrm.author = armature_object.get('vrm_author')
        # # self.vrm.contactInformation = armature_object['vrm_contactInformation']
        # # self.vrm.reference = armature_object['vrm_reference']
