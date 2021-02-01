from logging import currentframe, getLogger
logger = getLogger(__name__)
from typing import List, Optional, Dict
import bpy, mathutils
from ... import pyscene, formats, custom_rna
from ...struct_types import Float3
from .. import utils
from .material_exporter import MaterialExporter
from .export_map import ExportMap


class Exporter:
    def __init__(self) -> None:
        self.export_map = ExportMap()
        self.material_exporter = MaterialExporter(self.export_map)

    def _export_bone(self, skin: pyscene.Skin, matrix_world: mathutils.Matrix,
                     bone: bpy.types.Bone, parent: pyscene.Node):
        node = pyscene.Node(bone.name)
        self.export_map.add_node(bone, node)
        h = bone.head_local

        # Z-UP to Y-UP
        node.position = Float3(h.x, h.z, -h.y)

        parent.add_child(node)
        skin.joints.append(node)

        for child in bone.children:
            self._export_bone(skin, matrix_world, child, node)

    def _get_or_create_skin(self,
                            armature_object: bpy.types.Object) -> pyscene.Skin:
        '''
        Armature -> pyscene.Skin
        Bone[] -> pyscene.Skin.joints: List[pyscene.Node]
        '''
        if armature_object in self.export_map._skin_map:
            return self.export_map._skin_map[armature_object]

        name = armature_object.name
        if not name:
            name = 'skin'
        skin = pyscene.Skin(name)
        self.export_map._skin_map[armature_object] = skin

        with utils.disposable_mode(armature_object, 'POSE'):

            armature = armature_object.data
            if not isinstance(armature, bpy.types.Armature):
                raise Exception()
            for b in armature.bones:
                if not b.parent:
                    # root bone
                    parent = self.export_map._node_map[armature_object]
                    self._export_bone(skin, armature_object.matrix_world, b,
                                      parent)

        return skin

    def _export_mesh(self, o: bpy.types.Object, mesh: bpy.types.Mesh,
                     node: pyscene.Node) -> pyscene.FaceMesh:
        # copy
        new_obj = utils.clone(o)
        with utils.disposable(new_obj):
            new_mesh = new_obj.data
            if not isinstance(new_mesh, bpy.types.Mesh):
                raise Exception()

            # clear shape key
            new_obj.shape_key_clear()
            # otherwise
            # Error: Modifier cannot be applied to a mesh with shape keys

            # first create skin
            for m in new_obj.modifiers:
                if m.type == 'ARMATURE':
                    if m.object:
                        node.skin = self._get_or_create_skin(m.object)
                        break

            # apply modifiers
            utils.apply_modifiers(new_obj)

            # メッシュの三角形化
            new_mesh.calc_loop_triangles()
            new_mesh.update()
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
            bone_names = [b.name
                          for b in node.skin.joints] if node.skin else []
            facemesh = pyscene.FaceMesh(o.data.name, new_mesh.vertices,
                                        materials, o.vertex_groups, bone_names)
            # triangles
            uv_texture_layer = get_texture_layer(new_mesh.uv_layers)
            for i, triangle in enumerate(triangles):
                facemesh.add_triangle(triangle, uv_texture_layer)

            # shapekey
            if mesh.shape_keys:
                for key_block in mesh.shape_keys.key_blocks:
                    if key_block.name == 'Basis':
                        continue

                    shape_positions = (Float3 * len(mesh.vertices))()
                    for i, v in enumerate(key_block.data):
                        delta = v.co - mesh.vertices[i].co
                        shape_positions[i] = Float3(delta.x, delta.z, -delta.y)
                    facemesh.add_morph(key_block.name,
                                       shape_positions)  # type: ignore

            return facemesh

    # def _export_shapekey(
    #         self, o: bpy.types.Object, i: int,
    #         shape: bpy.types.ShapeKey) -> Sequence[bpy.types.MeshVertex]:
    #     logger.debug(f'{i}: {shape}')

    #     # TODO: modifier

    #     # # copy
    #     # new_obj = bpy_helper.clone_and_apply_transform(o)
    #     # with bpy_helper.disposable(new_obj):
    #     #     new_mesh: bpy.types.Mesh = new_obj.data

    #     #     # apply shape key
    #     #     bpy_helper.remove_shapekey_except(new_obj, i)
    #     #     new_obj.shape_key_clear()

    #     #     # apply modifiers
    #     #     bpy_helper.apply_modifiers(new_obj)

    #     #     # メッシュの三角形化
    #     #     if bpy.app.version[1] > 80:
    #     #         new_mesh.calc_loop_triangles()
    #     #         new_mesh.update()
    #     #     else:
    #     #         new_mesh.update(calc_loop_triangles=True)

    #     #     # POSITIONSを得る
    #     #     return [v for v in new_mesh.vertices]

    #     return shape.data

    def _export_object(self,
                       o: bpy.types.Object,
                       process_data: bool,
                       parent: Optional[pyscene.Node] = None) -> pyscene.Node:
        '''
        scan Node recursive
        '''

        if not process_data:

            # location = o.location
            # if o.parent:
            #     location -= o.parent.location
            node = pyscene.Node(o.name)
            self.export_map.add_node(o, node)
            if parent:
                parent.add_child(node)

        else:

            node = self.export_map._node_map[o]

            if not o.hide_viewport:
                if isinstance(o.data, bpy.types.Mesh):
                    mesh = self._export_mesh(o, o.data, node)
                    self.export_map.meshes.append(mesh)
                    node.mesh = mesh

                if isinstance(o.data, bpy.types.Armature):
                    with utils.disposable_mode(o, 'POSE'):
                        bones: Dict[str, pyscene.Node] = {}
                        for bone in o.pose.bones:
                            node = pyscene.Node(bone.name)
                            # self.export_map.nodes.append(node)
                            bones[bone.name] = node

                        def traverse_bone(bone: bpy.types.PoseBone,
                                          parent_name: Optional[str] = None):
                            # print(bone)

                            node = bones[bone.name]
                            # if parent_name:
                            #     bones[parent_name].add_child(node)

                            # custom property
                            humanoid_bone = bone.pyimpex_humanoid_bone
                            if humanoid_bone:
                                node.humanoid_bone = formats.HumanoidBones[
                                    humanoid_bone]

                            for child in bone.children:
                                traverse_bone(child, bone.name)

                        for bone in o.pose.bones:
                            if not bone.parent:
                                traverse_bone(bone)

                        # get vrm meta
                        meta: custom_rna.PYIMPEX_Meta = o.pyimpex_meta
                        vrm = pyscene.Vrm()
                        self.export_map.vrm = vrm
                        vrm.meta['version'] = meta.version
                        vrm.meta['title'] = meta.title
                        vrm.meta['author'] = meta.author
                        # # self.vrm.contactInformation = armature_object['vrm_contactInformation']
                        # # self.vrm.reference = armature_object['vrm_reference']

        for child in o.children:
            self._export_object(child, process_data, node)

        return node

    def scan(self, roots: List[bpy.types.Object]) -> None:
        # 1st pass exoprt objects
        for root in roots:
            self._export_object(root, False)
        # snd pass export mesh, skin
        for root in roots:
            self._export_object(root, True)

        # self._mesh_node_under_empty()
        # while True:
        #     if not self.export_map.remove_empty_leaf_nodes():
        #         break


def scan() -> ExportMap:
    targets = utils.objects_selected_or_roots()
    scanner = Exporter()
    scanner.scan(targets)
    return scanner.export_map
