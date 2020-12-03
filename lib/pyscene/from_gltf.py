from ctypes import c_ulong
from logging import getLogger
logger = getLogger(__name__)
from typing import Dict, NamedTuple, Optional, List, Any
import bpy, mathutils
from .. import formats
from .node import Node, Skin
from .material import UnlitMaterial, PBRMaterial, MToonMaterial, Texture, TextureUsage, BlendMode
from .submesh_mesh import SubmeshMesh, Submesh
from .index_map import IndexMap
from .modifier import before_import


def _skin_from_gltf(data: formats.GltfContext, skin_index: int,
                    nodes: List[Node]) -> Skin:
    gl_skin = data.gltf.skins[skin_index]

    name = gl_skin.name
    if not name:
        name = f'skin{skin_index}'
    skin = Skin(name)
    # if isinstance(gl_skin.skeleton, int):
    #     skin.parent_space = nodes[gl_skin.skeleton]
    skin.joints = [nodes[j] for j in gl_skin.joints]

    return skin


def _check_has_skin(prim: formats.gltf.MeshPrimitive) -> bool:
    if not prim.attributes.get('JOINTS_0'):
        return False
    if not prim.attributes.get('WEIGHTS_0'):
        return False
    return True


class Reader:
    def __init__(self, data: formats.GltfContext):
        self.data = data
        self.reader = formats.BytesReader(data)
        self.index_map = IndexMap(data.gltf)

    def get_vrm(self) -> Optional[formats.gltf.vrm]:
        if self.data.gltf.extensions:
            return self.data.gltf.extensions.VRM

    def _get_or_create_texture(self, image_index: int) -> Texture:
        texture = self.index_map.texture.get(image_index)
        if texture:
            return texture

        gl_image = self.data.gltf.images[image_index]
        name = gl_image.name

        if gl_image.uri:
            if not name:
                name = gl_image.uri
        if not name:
            name = f'image{image_index}'

        if isinstance(gl_image.bufferView, int):
            texture_bytes = self.reader.get_view_bytes(gl_image.bufferView)
            texture = Texture(name, texture_bytes)
        elif gl_image.uri:
            texture = Texture(name, self.data.dir / gl_image.uri)
        else:
            raise Exception('invalid gl_image')

        self.index_map.texture[image_index] = texture
        return texture

    def _get_or_create_material(
            self, material_index: Optional[int]) -> UnlitMaterial:
        if not isinstance(material_index, int):
            return UnlitMaterial(f'default')
        material = self.index_map.material.get(material_index)
        if material:
            return material

        def load_common_porperties(matrial: UnlitMaterial,
                                   gl_material: formats.gltf.Material):
            # color
            if gl_material.pbrMetallicRoughness.baseColorFactor:
                material.color.x = gl_material.pbrMetallicRoughness.baseColorFactor[
                    0]
                material.color.y = gl_material.pbrMetallicRoughness.baseColorFactor[
                    1]
                material.color.z = gl_material.pbrMetallicRoughness.baseColorFactor[
                    2]
                material.color.w = gl_material.pbrMetallicRoughness.baseColorFactor[
                    3]
            # texture
            if gl_material.pbrMetallicRoughness.baseColorTexture:
                image_index = gl_material.pbrMetallicRoughness.baseColorTexture.index
                texture = self._get_or_create_texture(image_index)
                texture.set_usage(TextureUsage.Color)
                material.color_texture = texture

            # alpha blending
            if isinstance(gl_material.alphaMode,
                          formats.gltf.MaterialAlphaMode):
                if gl_material.alphaMode == formats.gltf.MaterialAlphaMode.OPAQUE:
                    material.blend_mode = BlendMode.Opaque
                elif gl_material.alphaMode == formats.gltf.MaterialAlphaMode.BLEND:
                    material.blend_mode = BlendMode.AlphaBlend
                elif gl_material.alphaMode == formats.gltf.MaterialAlphaMode.MASK:
                    material.blend_mode = BlendMode.Mask
                    if isinstance(gl_material.alphaCutoff, float):
                        material.threshold = gl_material.alphaCutoff
                else:
                    raise NotImplementedError()
            else:
                pass

        # create
        gl_material = self.data.gltf.materials[material_index]

        vrm = self.get_vrm()
        vrm_material = None
        if vrm:
            vrm_material = vrm.materialProperties[material_index]

        name = gl_material.name
        if not name:
            name = f'material{material_index}'

        if vrm_material and vrm_material.shader == 'VRM/MToon':
            #
            # MToon
            #
            material = MToonMaterial(name)
            load_common_porperties(material, gl_material)
            for k, v in vrm_material.tagMap.items():
                if k == 'RenderType':
                    if v == 'Opaque':
                        pass
                    elif v == 'Transparent':
                        pass
                    elif v == 'TransparentCutout':
                        pass
                    else:
                        raise NotImplementedError()
                else:
                    raise NotImplementedError()
            for k, v in vrm_material.floatProperties.items():
                material.set_scalar(k, v)
            for k, v in vrm_material.textureProperties.items():
                material.set_texture(k, self._get_or_create_texture(v))
            for k, v in vrm_material.vectorProperties.items():
                material.set_vector4(k, v)

        elif gl_material.extensions and gl_material.extensions.KHR_materials_unlit:
            material = UnlitMaterial(name)
            load_common_porperties(material, gl_material)

        else:
            #
            # PBR
            #
            material = PBRMaterial(name)
            load_common_porperties(material, gl_material)
            # normal map
            if gl_material.normalTexture:
                material.normal_texture = self._get_or_create_texture(
                    gl_material.normalTexture.index)
                material.normal_texture.set_usage(TextureUsage.NormalMap)

            # emissive
            if gl_material.emissiveTexture:
                material.emissive_texture = self._get_or_create_texture(
                    gl_material.emissiveTexture.index)
                material.emissive_texture.set_usage(
                    TextureUsage.EmissiveTexture)
            if gl_material.emissiveFactor:
                material.emissive_color.x = gl_material.emissiveFactor[0]
                material.emissive_color.y = gl_material.emissiveFactor[1]
                material.emissive_color.z = gl_material.emissiveFactor[2]

            # metallic roughness
            if gl_material.pbrMetallicRoughness and gl_material.pbrMetallicRoughness.metallicRoughnessTexture:
                material.metallic_roughness_texture = self._get_or_create_texture(
                    gl_material.pbrMetallicRoughness.metallicRoughnessTexture.
                    index)
                material.metallic_roughness_texture.set_usage(
                    TextureUsage.MetallicRoughnessTexture)

            # oculusion
            if gl_material.occlusionTexture:
                material.occlusion_texture = self._get_or_create_texture(
                    gl_material.occlusionTexture.index)
                material.occlusion_texture.set_usage(
                    TextureUsage.OcclusionTexture)

        self.index_map.material[material_index] = material

        return material

    def load_submesh(self, data: formats.GltfContext,
                     mesh_index: int) -> SubmeshMesh:
        mesh = self.index_map.mesh.get(mesh_index)
        if mesh:
            return mesh

        m = data.gltf.meshes[mesh_index]
        name = m.name if m.name else f'mesh {mesh_index}'

        # check shared attributes
        shared = True
        attributes: Dict[str, int] = {}
        for prim in m.primitives:
            if not attributes:
                attributes = prim.attributes
            else:
                if attributes != prim.attributes:
                    shared = False
                    break
        logger.debug(f'SHARED: {shared}')

        def position_count(prim):
            accessor_index = prim.attributes['POSITION']
            return data.gltf.accessors[accessor_index].count

        def prim_index_count(prim: formats.gltf.MeshPrimitive) -> int:
            if not isinstance(prim.indices, int):
                return 0
            return data.gltf.accessors[prim.indices].count

        def add_indices(sm: SubmeshMesh, prim: formats.gltf.MeshPrimitive,
                        index_offset: int):
            # indices
            if not isinstance(prim.indices, int):
                raise Exception()
            mesh.indices.extend(self.reader.get_bytes(prim.indices))
            # submesh
            index_count = prim_index_count(prim)
            submesh = Submesh(index_offset, index_count,
                              self._get_or_create_material(prim.material))
            mesh.submeshes.append(submesh)
            return index_count

        has_skin = _check_has_skin(m.primitives[0])

        def get_morph_name(m, p, i) -> str:
            if p.extras and p.extras.targetNames and i < len(
                    p.extras.targetNames):
                return p.extras.targetNames[i]
            elif m.extras and m.extras.targetNames and i < len(
                    m.extras.targetNames):
                return p.extras.targetNames[i]

            # ToDo: target.position accessor/bufferView name ? see gltf sample
            return f'{i}'

        if shared:
            # share vertex buffer
            shared_prim = m.primitives[0]
            vertex_count = position_count(shared_prim)
            mesh = SubmeshMesh(name, vertex_count, has_skin)
            self.reader.read_attributes(mesh.attributes, 0, data,
                                        shared_prim.attributes)
            # morph target
            if shared_prim.targets:
                # TODO: each target has same vertex buffer
                for j, t in enumerate(shared_prim.targets):
                    morphtarget = mesh.get_or_create_morphtarget(j)
                    morphtarget.name = get_morph_name(m, shared_prim, j)
                    self.reader.read_attributes(morphtarget.attributes, 0,
                                                data, t)
            index_offset = 0
            for i, prim in enumerate(m.primitives):
                # indices
                index_offset += add_indices(mesh, prim, index_offset)

        else:
            # merge vertex buffer
            vertex_count = sum((position_count(prim) for prim in m.primitives),
                               0)
            mesh = SubmeshMesh(name, vertex_count, has_skin)

            offset = 0
            index_offset = 0
            for i, prim in enumerate(m.primitives):
                # vertex
                self.reader.read_attributes(mesh.attributes, offset, data,
                                            prim.attributes)
                offset += position_count(prim)
                # indices
                index_offset += add_indices(mesh, prim, index_offset)

                # morph target
                for prim in m.primitives:
                    if prim.targets:
                        for j, t in enumerate(prim.targets):
                            morphtarget = mesh.get_or_create_morphtarget(j)
                            morphtarget.name = get_morph_name(m, prim, j)
                            self.reader.read_attributes(
                                morphtarget.attributes, offset, data, t)

        self.index_map.mesh[mesh_index] = mesh

        return mesh


def load(data: formats.GltfContext) -> IndexMap:
    '''
    glTFを中間形式のSubmesh形式に変換する
    '''
    deserializer = Reader(data)

    def get_humanoid_bone(node_index: int) -> Optional[formats.HumanoidBones]:
        if not data.gltf.extensions:
            return
        vrm = data.gltf.extensions.VRM
        if not vrm:
            return

        for humanoid_bone in vrm.humanoid.humanBones:
            if humanoid_bone.node == node_index:
                if not humanoid_bone.bone:
                    raise Exception()
                return getattr(formats.HumanoidBones, humanoid_bone.bone)

    # mesh
    meshes: List[SubmeshMesh] = []
    if data.gltf.meshes:
        for i, m in enumerate(data.gltf.meshes):
            mesh = deserializer.load_submesh(data, i)
            meshes.append(mesh)

    # node
    nodes: List[Node] = []
    if data.gltf.nodes:
        for i, n in enumerate(data.gltf.nodes):
            name = n.name if n.name else f'node {i}'
            node = Node(name)
            deserializer.index_map.node[i] = node

            node.humanoid_bone = get_humanoid_bone(i)

            if n.translation:
                node.position.x = n.translation[0]
                node.position.y = n.translation[1]
                node.position.z = n.translation[2]

            if n.rotation:
                node.rotation.x = n.rotation[0]
                node.rotation.y = n.rotation[1]
                node.rotation.z = n.rotation[2]
                node.rotation.w = n.rotation[3]

            if n.scale:
                node.scale.x = n.scale[0]
                node.scale.y = n.scale[1]
                node.scale.z = n.scale[2]

            if n.matrix:
                m = n.matrix
                matrix = mathutils.Matrix(
                    ((m[0], m[4], m[8], m[12]), (m[1], m[5], m[9], m[13]),
                     (m[2], m[6], m[10], m[14]), (m[3], m[7], m[11], m[15])))
                t, q, s = matrix.decompose()
                node.position.x = t.x
                node.position.y = t.y
                node.position.z = t.z
                node.rotation.x = q.x
                node.rotation.y = q.y
                node.rotation.z = q.z
                node.rotation.w = q.w
                node.scale.x = s.x
                node.scale.y = s.y
                node.scale.z = s.z

            if isinstance(n.mesh, int):
                node.mesh = meshes[n.mesh]

            nodes.append(node)

        # build hierarchy
        for i, n in enumerate(data.gltf.nodes):
            if n.children:
                for c in n.children:
                    nodes[i].add_child(nodes[c])

        # create skin
        for i, n in enumerate(data.gltf.nodes):
            if isinstance(n.skin, int):
                skin = _skin_from_gltf(data, n.skin, nodes)
                nodes[i].skin = skin

    # prefix
    roots = deserializer.index_map.get_roots()
    before_import(roots, data.gltf.extensions != None)
    deserializer.index_map.load_vrm()

    return deserializer.index_map


def nodes_from_gltf(data: formats.GltfContext) -> List[Node]:
    return load(data).get_roots()
