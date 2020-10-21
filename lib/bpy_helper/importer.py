from logging import getLogger
logger = getLogger(__name__)
from typing import List, Optional, Dict, Tuple, Any
import bpy, mathutils
from ..formats import gltf
from ..bpy_helper import disposable_mode
from ..pyscene.node import Node
from ..pyscene.submesh_mesh import SubmeshMesh
from ..pyscene.material import Material, Texture

# def mod_v(v):
#     return (v[0], -v[2], v[1])

# def mod_q(q):
#     return mathutils.Quaternion(mod_v(q.axis), q.angle)


def _create_texture(manager: 'ImportManager', index: int,
                    texture: gltf.Texture) -> bpy.types.Texture:
    image = manager.gltf.images[texture.source]
    if image.uri:
        texture = load_image(image.uri, str(manager.base_dir))
    elif image.bufferView != -1:
        if not bpy.data.filepath:
            # can not extract image files
            #raise Exception('no bpy.data.filepath')
            texture = bpy.data.images.new('image', 128, 128)

        else:

            image_dir = pathlib.Path(
                bpy.data.filepath).absolute().parent / manager.path.stem
            if not image_dir.exists():
                image_dir.mkdir()

            data = manager.get_view_bytes(image.bufferView)
            image_path = image_dir / f'texture_{index:0>2}.png'
            if not image_path.exists():
                with image_path.open('wb') as w:
                    w.write(data)

            texture = load_image(image_path.name, str(image_path.parent))
    else:
        raise Exception("invalid image")
    progress.step()
    return texture


def _create_material(manager: 'ImportManager',
                     material: gltf.Material) -> bpy.types.Material:
    blender_material = bpy.data.materials.new(material.name)
    # blender_material['js'] = json.dumps(material.js, indent=2)

    # blender_material.use_nodes = True
    # tree = blender_material.node_tree

    # tree.nodes.remove(tree.nodes['Principled BSDF'])

    # getLogger('').disabled = True
    # groups = blender_groupnode_io.import_groups(gltf_pbr_node.groups)
    # getLogger('').disabled = False

    # bsdf = tree.nodes.new('ShaderNodeGroup')
    # bsdf.node_tree = groups['glTF Metallic Roughness']

    # tree.links.new(bsdf.outputs['Shader'],
    #                tree.nodes['Material Output'].inputs['Surface'])

    # def create_image_node(texture_index: int):
    #     # uv => tex
    #     image_node = tree.nodes.new(type='ShaderNodeTexImage')
    #     image_node.image = manager.textures[texture_index]
    #     tree.links.new(
    #         tree.nodes.new('ShaderNodeTexCoord').outputs['UV'],
    #         image_node.inputs['Vector'])
    #     return image_node

    # def bsdf_link_image(texture_index: int, input_name: str):
    #     texture = create_image_node(texture_index)
    #     tree.links.new(texture.outputs["Color"], bsdf.inputs[input_name])

    # if material.normalTexture:
    #     bsdf_link_image(material.normalTexture.index, 'Normal')

    # if material.occlusionTexture:
    #     bsdf_link_image(material.occlusionTexture.index, 'Occlusion')

    # if material.emissiveTexture:
    #     bsdf_link_image(material.emissiveTexture.index, 'Emissive')

    # pbr = material.pbrMetallicRoughness
    # if pbr:
    #     if pbr.baseColorTexture and pbr.baseColorFactor:
    #         # mix
    #         mix = tree.nodes.new(type='ShaderNodeMixRGB')
    #         mix.blend_type = 'MULTIPLY'
    #         mix.inputs[2].default_value = pbr.baseColorFactor

    #     elif pbr.baseColorTexture:
    #         bsdf_link_image(pbr.baseColorTexture.index, 'BaseColor')
    #     else:
    #         # factor
    #         pass

    #     if pbr.metallicRoughnessTexture:
    #         bsdf_link_image(pbr.metallicRoughnessTexture.index,
    #                         'MetallicRoughness')

    # progress.step()
    return blender_material


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


# create armature
def create_armature(self: Node, context, collection, view_layer,
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
                if get_child_is_connect(
                        child.blender_object.matrix_world.to_translation()):
                    child_is_connect = i
        else:
            child_is_connect = -1

        for i, child in enumerate(self.children):
            child.create_bone(skin, armature, self.blender_bone,
                              i == child_is_connect)


class Skin:
    def __init__(self, manager: 'ImportManager', skin: gltf.Skin) -> None:
        self.manager = manager
        self.skin = skin
        self.inverse_matrices: Any = None

    def get_matrix(self, joint: int) -> Any:
        if not self.inverse_matrices:
            self.inverse_matrices = self.manager.get_array(
                self.skin.inverseBindMatrices)
        m = self.inverse_matrices[joint]
        mat = mathutils.Matrix(
            ((m.f00, m.f10, m.f20, m.f30), (m.f01, m.f11, m.f21, m.f31),
             (m.f02, m.f12, m.f22, m.f32), (m.f03, m.f13, m.f23, m.f33)))
        # d = mat.decompose()
        return mat


class ImportManager:
    def __init__(self) -> None:
        self.textures: List[bpy.types.Texture] = []
        self.materials: List[bpy.types.Material] = []
        self.meshes: List[Tuple[bpy.types.Mesh, Any]] = []

        # yup_to_zup
        self.mod_v = lambda v: (v[0], -v[2], v[1])
        self.mod_q = lambda q: mathutils.Quaternion(self.mod_v(q.axis), q.angle
                                                    )
        self._buffer_map: Dict[str, bytes] = {}

    def load_textures(self):
        '''
        gltf.textures => List[bpy.types.Texture]
        '''
        if not self.gltf.textures:
            return
        self.textures = [
            _create_texture(self, i, texture)
            for i, texture in enumerate(self.gltf.textures)
        ]

    def load_materials(self):
        '''
        gltf.materials => List[bpy.types.Material]
        '''
        if not self.gltf.materials:
            return
        self.materials = [
            _create_material(self, material)
            for material in self.gltf.materials
        ]

    def load_meshes(self):
        self.meshes = [_create_mesh(self, mesh) for mesh in self.gltf.meshes]

    def load_objects(self, context: bpy.types.Context, roots: List[Node]):
        # collection
        view_layer = context.view_layer
        if hasattr(view_layer,
                   'collections') and view_layer.collections.active:
            collection = view_layer.collections.active.collection
        else:
            collection = context.scene.collection
            # view_layer.collections.link(collection)

        # setup
        # nodes = [
        #     create_node(gltf_node)
        #     for i, gltf_node in enumerate(self.gltf.nodes)
        # ]

        # set parents
        # for gltf_node, node in zip(self.gltf.nodes, nodes):
        #     for child_index in gltf_node.children:
        #         child = nodes[child_index]
        #         node.add_child(child)

        # check root
        # roots = [node for node in enumerate(nodes) if not node[1].parent]
        # if len(roots) != 1:
        #     root = Node(len(nodes), gltf.Node({'name': '__root__'}))
        #     for _, node in roots:
        #         root.children.append(node)
        #         node.parent = root
        # else:
        #     root = nodes[0]
        for root in roots:
            create_object(root, collection, self)

        # def get_root(skin: gltf.Skin) -> Optional[Node]:

        #     root = None

        #     for joint in skin.joints:
        #         node = nodes[joint]
        #         if not root:
        #             root = node
        #         else:
        #             if node in root.get_ancestors():
        #                 root = node

        #     return root

        # create armatures
        # root_skin = gltf.Skin.from_dict({'name': 'skin'})

        # for skin in self.gltf.skins:
        #     for joint in skin.joints:
        #         if joint not in root_skin.joints:
        #             root_skin.joints.append(joint)
        # skeleton = get_root(root_skin)

        # if skeleton:
        #     create_armature(skeleton, context, collection, view_layer,
        #                     root_skin)

        # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    def get_view_bytes(self, view_index: int) -> bytes:
        view = self.gltf.bufferViews[view_index]
        buffer = self.gltf.buffers[view.buffer]
        if buffer.uri:
            if buffer.uri in self._buffer_map:
                return self._buffer_map[
                    buffer.uri][view.byteOffset:view.byteOffset +
                                view.byteLength]
            else:
                path = self.base_dir / buffer.uri
                with path.open('rb') as f:
                    data = f.read()
                    self._buffer_map[buffer.uri] = data
                    return data[view.byteOffset:view.byteOffset +
                                view.byteLength]
        else:
            return self.body[view.byteOffset:view.byteOffset + view.byteLength]

    def get_array(self, accessor_index: int):
        accessor = self.gltf.accessors[
            accessor_index] if self.gltf.accessors else None
        if not accessor:
            raise Exception()
        accessor_byte_len = get_accessor_byteslen(accessor)
        if not isinstance(accessor.bufferView, int):
            raise Exception()
        view_bytes = self.get_view_bytes(accessor.bufferView)
        segment = view_bytes[accessor.byteOffset:accessor.byteOffset +
                             accessor_byte_len]

        if accessor.type == gltf.AccessorType.SCALAR:
            if (accessor.componentType == gltf.AccessorComponentType.SHORT
                    or accessor.componentType
                    == gltf.AccessorComponentType.UNSIGNED_SHORT):
                return (ctypes.c_ushort *  # type: ignore
                        accessor.count).from_buffer_copy(segment)
            elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_INT:
                return (ctypes.c_uint *  # type: ignore
                        accessor.count).from_buffer_copy(segment)
        elif accessor.type == gltf.AccessorType.VEC2:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float2 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        elif accessor.type == gltf.AccessorType.VEC3:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float3 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        elif accessor.type == gltf.AccessorType.VEC4:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float4 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

            elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_SHORT:
                return (UShort4 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        elif accessor.type == gltf.AccessorType.MAT4:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Mat16 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        raise NotImplementedError()


class Importer:
    '''
    bpy.types.Object, Mesh, Material, Texture を作成する
    '''
    def __init__(self, context: bpy.types.Context):
        view_layer = context.view_layer
        if hasattr(view_layer,
                   'collections') and view_layer.collections.active:
            self.collection = view_layer.collections.active.collection
        else:
            self.collection = context.scene.collection
            # view_layer.collections.link(collection)

        self.obj_map: Dict[Node, bpy.types.Object] = {}
        self.mesh_map: Dict[SubmeshMesh, bpy.types.Mesh] = {}
        self.material_map: Dict[Material, bpy.types.Material] = {}
        self.image_map: Dict[Texture, bpy.types.Image] = {}

    def _get_or_create_image(self, texture: Texture) -> bpy.types.Image:
        bl_image = self.image_map.get(texture)
        if bl_image:
            return bl_image

        image = texture.image
        bl_image = bpy.data.images.new(texture.name,
                                       width=image.width,
                                       height=image.height)
        self.image_map[texture] = bl_image
        return bl_image

    def _get_or_create_material(self,
                                material: Material) -> bpy.types.Material:
        bl_material = self.material_map.get(material)
        if bl_material:
            return bl_material

        bl_material = bpy.data.materials.new(material.name)
        self.material_map[material] = bl_material

        if material.texture and material.texture.image:
            # texture
            bl_texture = bpy.data.textures.new(material.texture.name,
                                               type='IMAGE')
            bl_texture.image = self._get_or_create_image(material.texture)
            # require node
            # bl_material.texture_slots.add().texture = bl_texture

        return bl_material

    def _get_or_create_mesh(self, mesh: SubmeshMesh) -> bpy.types.Mesh:
        bl_mesh = self.mesh_map.get(mesh)
        if bl_mesh:
            return bl_mesh

        bl_mesh = bpy.data.meshes.new(mesh.name)
        self.mesh_map[mesh] = bl_mesh

        for submesh in mesh.submeshes:
            bl_material = self._get_or_create_material(submesh.material)
            bl_mesh.materials.append(bl_material)

        attributes = mesh.attributes

        bl_mesh.vertices.add(attributes.get_vertex_count())
        bl_mesh.vertices.foreach_set(
            "co", [n for v in attributes.position for n in (v.x, v.y, v.z)])
        bl_mesh.vertices.foreach_set(
            "normal", [n for v in attributes.normal for n in (v.x, v.y, v.z)])

        bl_mesh.loops.add(len(mesh.indices))
        bl_mesh.loops.foreach_set("vertex_index", mesh.indices)

        triangle_count = len(mesh.indices) // 3
        bl_mesh.polygons.add(triangle_count)
        starts = [i * 3 for i in range(triangle_count)]
        bl_mesh.polygons.foreach_set("loop_start", starts)
        total = [3 for _ in range(triangle_count)]
        bl_mesh.polygons.foreach_set("loop_total", total)

        # blen_uvs = bl_mesh.uv_layers.new()
        # for blen_poly in bl_mesh.polygons:
        #     blen_poly.use_smooth = True
        #     blen_poly.material_index = attributes.get_submesh_from_face(
        #         blen_poly.index)
        #     for lidx in blen_poly.loop_indices:
        #         index = attributes.indices[lidx]
        #         # vertex uv to face uv
        #         uv = attributes.uv[index]
        #         blen_uvs.data[lidx].uv = (uv.x, uv.y)  # vertical flip uv

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
            bl_obj = bpy.data.objects.new(node.name, bl_mesh)
        else:
            # empty
            bl_obj = bpy.data.objects.new(node.name, None)
            bl_obj.empty_display_size = 0.1
            # self.blender_object.empty_draw_type = 'PLAIN_AXES'
        self.collection.objects.link(bl_obj)
        bl_obj.select_set(True)
        self.obj_map[node] = bl_obj

        # parent
        if node.parent:
            bl_obj.parent = self.obj_map.get(node.parent)

        # TRS
        # obj.location = node.position
        # with disposable_mode(obj, 'QUATERNION'):
        #     obj.rotation_quaternion = node.rotation
        # obj.scale = node.scale

    def traverse(self, node: Node, parent: Optional[Node] = None):
        self._create_object(node)
        for child in node.children:
            self.traverse(child, node)


# def _setup_skinning(blender_object: bpy.types.Object,
#                     attributes: gltf_buffer.VertexBuffer,
#                     bone_names: List[str],
#                     armature_object: bpy.types.Object) -> None:
#     # create vertex groups
#     for bone_name in bone_names:
#         if bone_name:
#             blender_object.vertex_groups.new(name=bone_name)

#     idx_already_done: Set[int] = set()

#     # each face
#     for poly in blender_object.data.polygons:
#         # face vertex index
#         for loop_idx in range(poly.loop_start,
#                               poly.loop_start + poly.loop_total):
#             loop = blender_object.data.loops[loop_idx]
#             vert_idx = loop.vertex_index
#             if vert_idx < 0:
#                 raise Exception()
#             if vert_idx >= len(attributes.joints):
#                 raise Exception()

#             if vert_idx in idx_already_done:
#                 continue
#             idx_already_done.add(vert_idx)

#             cpt = 0
#             for joint_idx in attributes.joints[vert_idx]:
#                 if cpt > 3:
#                     break
#                 weight_val = attributes.weights[vert_idx][cpt]
#                 if weight_val != 0.0:
#                     # It can be a problem to assign weights of 0
#                     # for bone index 0, if there is always 4 indices in joint_ tuple
#                     bone_name = bone_names[joint_idx]
#                     if bone_name:
#                         group = blender_object.vertex_groups[bone_name]
#                         group.add([vert_idx], weight_val, 'REPLACE')
#                 cpt += 1

#     # select
#     # for obj_sel in bpy.context.scene.objects:
#     #    obj_sel.select = False
#     #blender_object.select = True
#     #bpy.context.scene.objects.active = blender_object

#     modifier = blender_object.modifiers.new(name="Armature", type="ARMATURE")
#     modifier.object = armature_object

# def _remove_empty(node: Node):
#     for i in range(len(node.children) - 1, -1, -1):
#         child = node.children[i]
#         _remove_empty(child)

#     if node.children:
#         return
#     if node.blender_armature:
#         return
#     if node.blender_object.data:
#         return

#     # remove empty
#     bpy.data.objects.remove(node.blender_object, do_unlink=True)
#     if node.parent:
#         node.parent.children.remove(node)


def import_roots(context: bpy.types.Context, roots: List[Node]):
    importer = Importer(context)
    for root in roots:
        importer.traverse(root)

    # manager.load_textures()
    # manager.load_materials()
    # manager.load_meshes()
    # for m, _ in manager.meshes:
    #     logger.debug(f'[{m.name}: {len(m.vertices)}]vertices')
    # nodes, root = manager.load_objects(context, roots)

    # # skinning
    # armature_object = next(node for node in root.traverse()
    #                         if node.blender_armature)

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