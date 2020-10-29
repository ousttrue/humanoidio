from logging import getLogger
logger = getLogger(__name__)
from typing import Dict, Optional, List
import bpy, mathutils
from .. import formats
from .. import pyscene


def _skin_from_gltf(data: formats.GltfContext, skin_index: int,
                    nodes: List[pyscene.Node]) -> pyscene.Skin:
    gl_skin = data.gltf.skins[skin_index]

    name = gl_skin.name
    if not name:
        name = f'skin{skin_index}'
    skin = pyscene.Skin(name)
    if isinstance(gl_skin.skeleton, int):
        skin.parent_space = nodes[gl_skin.skeleton]
    skin.root_joints = [
        nodes[j] for j in gl_skin.joints if not nodes[j].parent
    ]
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
        # gltf の url 参照の外部ファイルバッファをキャッシュする
        self._material_map: Dict[int, pyscene.Material] = {}
        self._texture_map: Dict[int, pyscene.Texture] = {}

    def _get_or_create_texture(self, image_index: int) -> pyscene.Texture:
        texture = self._texture_map.get(image_index)
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
            texture = pyscene.Texture(name, texture_bytes)
        elif gl_image.uri:
            texture = pyscene.Texture(name, self.data.dir / gl_image.uri)
        else:
            raise Exception('invalid gl_image')

        self._texture_map[image_index] = texture
        return texture

    def _get_or_create_material(
            self, material_index: Optional[int]) -> pyscene.Material:
        if not isinstance(material_index, int):
            return pyscene.Material(f'default')
        material = self._material_map.get(material_index)
        if material:
            return material

        # create
        gl_material = self.data.gltf.materials[material_index]
        name = gl_material.name
        if not name:
            name = f'material{material_index}'
        if gl_material.extensions and 'KHR_materials_unlit' in gl_material.extensions:
            material = pyscene.Material(name)
        else:
            material = pyscene.PBRMaterial(name)

            # normal map
            if gl_material.normalTexture:
                material.normal_map = self._get_or_create_texture(
                    gl_material.normalTexture.index)
                material.normal_map.set_usage(pyscene.TextureUsage.NormalMap)

            # emissive
            if gl_material.emissiveTexture:
                material.emissive_texture = self._get_or_create_texture(
                    gl_material.emissiveTexture.index)
                material.emissive_texture.set_usage(
                    pyscene.TextureUsage.EmissiveTexture)

            # metallic roughness
            if gl_material.pbrMetallicRoughness and gl_material.pbrMetallicRoughness.metallicRoughnessTexture:
                material.metallic_roughness_texture = self._get_or_create_texture(
                    gl_material.pbrMetallicRoughness.metallicRoughnessTexture.
                    index)
                material.metallic_roughness_texture.set_usage(
                    pyscene.TextureUsage.MetallicRoughnessTexture)

            # oculusion
            if gl_material.occlusionTexture:
                material.occlusion_texture = self._get_or_create_texture(
                    gl_material.occlusionTexture.index)
                material.occlusion_texture.set_usage(
                    pyscene.TextureUsage.OcclusionTexture)

        self._material_map[material_index] = material

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
            texture.set_usage(pyscene.TextureUsage.Color)
            material.texture = texture

        # alpha blending
        if isinstance(gl_material.alphaMode, formats.gltf.MaterialAlphaMode):
            if gl_material.alphaMode == formats.gltf.MaterialAlphaMode.OPAQUE:
                material.blend_mode = pyscene.BlendMode.Opaque
            elif gl_material.alphaMode == formats.gltf.MaterialAlphaMode.BLEND:
                material.blend_mode = pyscene.BlendMode.AlphaBlend
            elif gl_material.alphaMode == formats.gltf.MaterialAlphaMode.MASK:
                material.blend_mode = pyscene.BlendMode.Mask
                if isinstance(gl_material.alphaCutoff, float):
                    material.threshold = gl_material.alphaCutoff
            else:
                raise NotImplementedError()
        else:
            pass

        return material

    def load_submesh(self, data: formats.GltfContext,
                     mesh_index: int) -> pyscene.SubmeshMesh:
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

        def add_indices(sm: pyscene.SubmeshMesh,
                        prim: formats.gltf.MeshPrimitive, index_offset: int):
            # indices
            if not isinstance(prim.indices, int):
                raise Exception()
            mesh.indices.extend(self.reader.get_bytes(prim.indices))
            # submesh
            index_count = prim_index_count(prim)
            submesh = pyscene.Submesh(
                index_offset, index_count,
                self._get_or_create_material(prim.material))
            mesh.submeshes.append(submesh)
            return index_count

        has_skin = _check_has_skin(m.primitives[0])

        if shared:
            # share vertex buffer
            shared_prim = m.primitives[0]
            vertex_count = position_count(shared_prim)
            mesh = pyscene.SubmeshMesh(name, vertex_count, has_skin)
            self.reader.read_attributes(mesh.attributes, 0, data,
                                        shared_prim.attributes)
            # morph target
            if shared_prim.targets:
                # TODO: each target has same vertex buffer
                for j, t in enumerate(shared_prim.targets):
                    morphtarget = mesh.get_or_create_morphtarget(j)
                    self.reader.read_attributes(morphtarget.attributes, 0,
                                                data, t)
                    # TODO: morph target name
            index_offset = 0
            for i, prim in enumerate(m.primitives):
                # indices
                index_offset += add_indices(mesh, prim, index_offset)

        else:
            # merge vertex buffer
            vertex_count = sum((position_count(prim) for prim in m.primitives),
                               0)
            mesh = pyscene.SubmeshMesh(name, vertex_count, has_skin)

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
                            self.reader.read_attributes(
                                morphtarget.attributes, offset, data, t)
                            # TODO: morph target name

        return mesh


def nodes_from_gltf(data: formats.GltfContext) -> List[pyscene.Node]:
    '''
    glTFを中間形式のSubmesh形式に変換する
    '''
    deserializer = Reader(data)

    # mesh
    meshes: List[pyscene.SubmeshMesh] = []
    if data.gltf.meshes:
        for i, m in enumerate(data.gltf.meshes):
            mesh = deserializer.load_submesh(data, i)
            meshes.append(mesh)

    # node
    nodes: List[pyscene.Node] = []
    if data.gltf.nodes:
        for i, n in enumerate(data.gltf.nodes):
            name = n.name if n.name else f'node {i}'
            node = pyscene.Node(name)

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
                if not skin.name:
                    skin.name = n.name
                nodes[i].skin = skin

    # scene
    scene = data.gltf.scenes[data.gltf.scene if data.gltf.scene else 0]
    if not scene.nodes:
        return []
    return [nodes[root] for root in scene.nodes]
