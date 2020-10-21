from logging import getLogger
logger = getLogger(__name__)
from contextlib import contextmanager
from typing import List, Optional, Dict, Tuple, Any, Set
import bpy, mathutils
from ..formats import gltf
from ..bpy_helper import disposable_mode
from ..pyscene.node import Node, Skin
from ..pyscene.submesh_mesh import SubmeshMesh
from ..pyscene.material import Material, PBRMaterial, Texture
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


class VertexBuffer:
    def __init__(self, manager, mesh: gltf.Mesh) -> None:
        # check shared attributes
        attributes: Dict[str, int] = {}
        shared = True
        for prim in mesh.primitives:
            if not attributes:
                attributes = prim.attributes
            else:
                if attributes != prim.attributes:
                    shared = False
                    break
        logger.debug(f'SHARED: {shared}')

        #submeshes = [Submesh(path, gltf, prim) for prim in mesh.primitives]

        # merge submesh
        def position_count(prim):
            accessor_index = prim.attributes['POSITION']
            return manager.gltf.accessors[accessor_index].count

        pos_count = sum((position_count(prim) for prim in mesh.primitives), 0)

        self.pos = (ctypes.c_float * (pos_count * 3))()
        self.nom = (ctypes.c_float * (pos_count * 3))()
        self.uv = (Float2 * pos_count)()
        self.joints = (UShort4 * pos_count)()
        self.weights = (Float4 * pos_count)()

        def index_count(prim: gltf.MeshPrimitive) -> int:
            return manager.gltf.accessors[prim.indices].count

        index_count = sum(
            (
                index_count(prim)  # type: ignore
                for prim in mesh.primitives),
            0)
        self.indices = (ctypes.c_int * index_count)()  # type: ignore
        self.submesh_index_count: List[int] = []

        pos_index = 0
        nom_index = 0
        uv_index = 0
        indices_index = 0
        offset = 0
        joint_index = 0
        for prim in mesh.primitives:
            #
            # attributes
            #
            pos = manager.get_array(prim.attributes['POSITION'])

            nom = None
            if 'NORMAL' in prim.attributes:
                nom = manager.get_array(prim.attributes['NORMAL'])
                if len(nom) != len(pos):
                    raise Exception("len(nom) different from len(pos)")

            uv = None
            if 'TEXCOORD_0' in prim.attributes:
                uv = manager.get_array(prim.attributes['TEXCOORD_0'])
                if len(uv) != len(pos):
                    raise Exception("len(uv) different from len(pos)")

            joints = None
            if 'JOINTS_0' in prim.attributes:
                joints = manager.get_array(prim.attributes['JOINTS_0'])
                if len(joints) != len(pos):
                    raise Exception("len(joints) different from len(pos)")

            weights = None
            if 'WEIGHTS_0' in prim.attributes:
                weights = manager.get_array(prim.attributes['WEIGHTS_0'])
                if len(weights) != len(pos):
                    raise Exception("len(weights) different from len(pos)")

            for p in pos:
                self.pos[pos_index] = p.x
                pos_index += 1
                self.pos[pos_index] = -p.z
                pos_index += 1
                self.pos[pos_index] = p.y
                pos_index += 1

            if nom:
                for n in nom:
                    self.nom[nom_index] = n.x
                    nom_index += 1
                    self.nom[nom_index] = -n.z
                    nom_index += 1
                    self.nom[nom_index] = n.y
                    nom_index += 1

            if uv:
                for xy in uv:
                    xy.y = 1.0 - xy.y  # flip vertical
                    self.uv[uv_index] = xy
                    uv_index += 1

            if joints and weights:
                for joint, weight in zip(joints, weights):
                    self.joints[joint_index] = joint
                    self.weights[joint_index] = weight
                    joint_index += 1

            #
            # indices
            #
            indices = manager.get_array(prim.indices)
            for i in indices:
                self.indices[indices_index] = offset + i
                indices_index += 1

            self.submesh_index_count.append(len(indices))
            offset += len(pos)

    def get_submesh_from_face(self, face_index) -> int:
        target = face_index * 3
        n = 0
        for i, count in enumerate(self.submesh_index_count):
            n += count
            if target < n:
                return i
        return -1


def _create_mesh(manager: 'ImportManager',
                 mesh: gltf.Mesh) -> Tuple[bpy.types.Mesh, VertexBuffer]:
    blender_mesh = bpy.data.meshes.new(mesh.name)
    materials = [manager.materials[prim.material] for prim in mesh.primitives]
    for m in materials:
        blender_mesh.materials.append(m)

    attributes = VertexBuffer(manager, mesh)

    blender_mesh.vertices.add(len(attributes.pos) / 3)
    blender_mesh.vertices.foreach_set("co", attributes.pos)
    blender_mesh.vertices.foreach_set("normal", attributes.nom)

    blender_mesh.loops.add(len(attributes.indices))
    blender_mesh.loops.foreach_set("vertex_index", attributes.indices)

    triangle_count = int(len(attributes.indices) / 3)
    blender_mesh.polygons.add(triangle_count)
    starts = [i * 3 for i in range(triangle_count)]
    blender_mesh.polygons.foreach_set("loop_start", starts)
    total = [3 for _ in range(triangle_count)]
    blender_mesh.polygons.foreach_set("loop_total", total)

    blen_uvs = blender_mesh.uv_layers.new()
    for blen_poly in blender_mesh.polygons:
        blen_poly.use_smooth = True
        blen_poly.material_index = attributes.get_submesh_from_face(
            blen_poly.index)
        for lidx in blen_poly.loop_indices:
            index = attributes.indices[lidx]
            # vertex uv to face uv
            uv = attributes.uv[index]
            blen_uvs.data[lidx].uv = (uv.x, uv.y)  # vertical flip uv

    # *Very* important to not remove lnors here!
    blender_mesh.validate(clean_customdata=False)
    blender_mesh.update()

    return blender_mesh, attributes


# class ImportManager:
#     def __init__(self) -> None:
#         self.textures: List[bpy.types.Texture] = []
#         self.materials: List[bpy.types.Material] = []
#         self.meshes: List[Tuple[bpy.types.Mesh, Any]] = []

#         # yup_to_zup
#         self.mod_v = lambda v: (v[0], -v[2], v[1])
#         self.mod_q = lambda q: mathutils.Quaternion(self.mod_v(q.axis), q.angle
#                                                     )
#         self._buffer_map: Dict[str, bytes] = {}

#     def load_textures(self):
#         '''
#         gltf.textures => List[bpy.types.Texture]
#         '''
#         if not self.gltf.textures:
#             return
#         self.textures = [
#             _create_texture(self, i, texture)
#             for i, texture in enumerate(self.gltf.textures)
#         ]

#     def load_materials(self):
#         '''
#         gltf.materials => List[bpy.types.Material]
#         '''
#         if not self.gltf.materials:
#             return
#         self.materials = [
#             _create_material(self, material)
#             for material in self.gltf.materials
#         ]

#     def load_meshes(self):
#         self.meshes = [_create_mesh(self, mesh) for mesh in self.gltf.meshes]

#     def get_view_bytes(self, view_index: int) -> bytes:
#         view = self.gltf.bufferViews[view_index]
#         buffer = self.gltf.buffers[view.buffer]
#         if buffer.uri:
#             if buffer.uri in self._buffer_map:
#                 return self._buffer_map[
#                     buffer.uri][view.byteOffset:view.byteOffset +
#                                 view.byteLength]
#             else:
#                 path = self.base_dir / buffer.uri
#                 with path.open('rb') as f:
#                     data = f.read()
#                     self._buffer_map[buffer.uri] = data
#                     return data[view.byteOffset:view.byteOffset +
#                                 view.byteLength]
#         else:
#             return self.body[view.byteOffset:view.byteOffset + view.byteLength]

#     def get_array(self, accessor_index: int):
#         accessor = self.gltf.accessors[
#             accessor_index] if self.gltf.accessors else None
#         if not accessor:
#             raise Exception()
#         accessor_byte_len = get_accessor_byteslen(accessor)
#         if not isinstance(accessor.bufferView, int):
#             raise Exception()
#         view_bytes = self.get_view_bytes(accessor.bufferView)
#         segment = view_bytes[accessor.byteOffset:accessor.byteOffset +
#                              accessor_byte_len]

#         if accessor.type == gltf.AccessorType.SCALAR:
#             if (accessor.componentType == gltf.AccessorComponentType.SHORT
#                     or accessor.componentType
#                     == gltf.AccessorComponentType.UNSIGNED_SHORT):
#                 return (ctypes.c_ushort *  # type: ignore
#                         accessor.count).from_buffer_copy(segment)
#             elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_INT:
#                 return (ctypes.c_uint *  # type: ignore
#                         accessor.count).from_buffer_copy(segment)
#         elif accessor.type == gltf.AccessorType.VEC2:
#             if accessor.componentType == gltf.AccessorComponentType.FLOAT:
#                 return (Float2 *  # type: ignore
#                         accessor.count).from_buffer_copy(segment)

#         elif accessor.type == gltf.AccessorType.VEC3:
#             if accessor.componentType == gltf.AccessorComponentType.FLOAT:
#                 return (Float3 *  # type: ignore
#                         accessor.count).from_buffer_copy(segment)

#         elif accessor.type == gltf.AccessorType.VEC4:
#             if accessor.componentType == gltf.AccessorComponentType.FLOAT:
#                 return (Float4 *  # type: ignore
#                         accessor.count).from_buffer_copy(segment)

#             elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_SHORT:
#                 return (UShort4 *  # type: ignore
#                         accessor.count).from_buffer_copy(segment)

#         elif accessor.type == gltf.AccessorType.MAT4:
#             if accessor.componentType == gltf.AccessorComponentType.FLOAT:
#                 return (Mat16 *  # type: ignore
#                         accessor.count).from_buffer_copy(segment)

#         raise NotImplementedError()


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

    def execute(self, roots: List[Node]):
        for root in roots:
            self._create_tree(root)

        # skinning
        for root in roots:
            skin_node = next(node for node in root.traverse() if node.skin)
            if skin_node.skin:
                self._create_armature(skin_node, skin_node.skin)
            else:
                raise Exception()

        for n, o in self.obj_map.items():
            if o.type == 'MESH' and n.skin:
                self._setup_skinning(n)

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

        # select
        # for obj_sel in bpy.context.scene.objects:
        #    obj_sel.select = False
        #bl_object.select = True
        #bpy.context.scene.objects.active = bl_object

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
            "co", [n for v in attributes.position for n in (v.x, v.y, v.z)])
        bl_mesh.vertices.foreach_set(
            "normal", [n for v in attributes.normal for n in (v.x, v.y, v.z)])

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
            bl_poly.use_smooth = True  # enable vertex normal
            bl_poly.material_index = material_index_map.get(
                mesh.submeshes[submesh_index].material)
            for lidx in bl_poly.loop_indices:
                tmp.append(lidx)
                vertex_index = mesh.indices[lidx]
                # vertex uv to face uv
                uv = attributes.texcoord[vertex_index]
                bl_texcord.data[lidx].uv = (uv.x, uv.y)  # vertical flip uv
            submesh_count += 1

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
