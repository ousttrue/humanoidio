'''
* serialize: pyscene => GLTF
* deserialize: GLTF => pyscene
'''
import pathlib
from logging import getLogger
logger = getLogger(__name__)
from typing import List, Optional, Tuple, Any, Iterator, Dict, Union
import bpy, mathutils
from ... import formats, pyscene
from ...pyscene.material import BlendMode, UnlitMaterial, PBRMaterial, Texture
from ...struct_types import Float3, Mat4
from .export_map import ExportMap
from .to_submesh import facemesh_to_submesh

GLTF_VERSION = '2.0'
GENERATOR_NAME = 'pyimpex'


def get_png_bytes(texture: Texture) -> bytes:
    if isinstance(texture.url_or_bytes, bytes):
        return texture.url_or_bytes

    if isinstance(texture.url_or_bytes, pathlib.Path):
        return texture.url_or_bytes.read_bytes()

    raise NotImplementedError()


class MaterialExporter:
    def __init__(self):
        self.images: List[formats.gltf.Image] = []
        self.samplers: List[formats.gltf.Sampler] = []
        self.textures: List[formats.gltf.Texture] = []
        self.materials: List[formats.gltf.Material] = []
        self.texture_map: Dict[Texture, int] = {}
        self.material_map: Dict[UnlitMaterial, int] = {}

    def get_or_create_material(self, src: UnlitMaterial,
                               buffer: formats.BufferManager) -> int:
        material_index = self.material_map.get(src)
        if isinstance(material_index, int):
            return material_index

        #
        # 共通項目
        #
        color = [0.5, 0.5, 0.5, 1.0]
        if src.color:
            color = [src.color.x, src.color.y, src.color.z, src.color.w]
        color_texture = None
        if src.color_texture:
            texture_index = self._get_or_create_texture(
                src.color_texture, buffer)
            color_texture = formats.gltf.TextureInfo(index=texture_index)

        alpha_mode = formats.gltf.MaterialAlphaMode.OPAQUE
        if src.blend_mode == BlendMode.AlphaBlend:
            alpha_mode = formats.gltf.MaterialAlphaMode.BLEND
        elif src.blend_mode == BlendMode.Mask:
            alpha_mode = formats.gltf.MaterialAlphaMode.MASK

        if isinstance(src, PBRMaterial):
            #
            # PBR
            #
            metallic_roughness_texture = None
            if src.metallic_roughness_texture:
                metallic_roughness_texture_index = self._get_or_create_texture(
                    src.metallic_roughness_texture, buffer)
                metallic_roughness_texture = formats.gltf.TextureInfo(
                    index=metallic_roughness_texture_index)

            normal_texture = None
            if src.normal_texture:
                normal_texture_index = self._get_or_create_texture(
                    src.normal_texture, buffer)
                normal_texture = formats.gltf.MaterialNormalTextureInfo(
                    index=normal_texture_index)

            occlusion_texture = None
            if src.occlusion_texture:
                occlusion_texture_index = self._get_or_create_texture(
                    src.occlusion_texture, buffer)
                occlusion_texture = formats.gltf.MaterialOcclusionTextureInfo(
                    index=occlusion_texture_index,
                    strength=src.occlusion_strength)

            emission = [
                src.emissive_color.x, src.emissive_color.y,
                src.emissive_color.z
            ]
            emissive_texture = None
            if src.emissive_texture:
                emissive_texture_index = self._get_or_create_texture(
                    src.emissive_texture, buffer)
                emissive_texture = formats.gltf.TextureInfo(
                    index=emissive_texture_index)

            gltf_material = formats.gltf.Material(
                name=src.name,
                pbrMetallicRoughness=formats.gltf.MaterialPBRMetallicRoughness(
                    baseColorFactor=color,
                    baseColorTexture=color_texture,
                    metallicFactor=0,
                    roughnessFactor=0.9,
                    metallicRoughnessTexture=metallic_roughness_texture,
                    extensions={},
                    extras={}),
                normalTexture=normal_texture,
                occlusionTexture=occlusion_texture,
                emissiveTexture=emissive_texture,
                emissiveFactor=emission,
                alphaMode=alpha_mode,
                alphaCutoff=src.threshold,
                doubleSided=src.double_sided,
                extensions=None,
                extras=None)

        else:
            # Unlit
            gltf_material = formats.gltf.Material(
                name=src.name,
                pbrMetallicRoughness=formats.gltf.MaterialPBRMetallicRoughness(
                    baseColorFactor=color,
                    baseColorTexture=color_texture,
                    metallicFactor=0,
                    roughnessFactor=0.9,
                    metallicRoughnessTexture=None,
                    extensions={},
                    extras={}),
                normalTexture=None,
                occlusionTexture=None,
                emissiveTexture=None,
                emissiveFactor=None,
                alphaMode=alpha_mode,
                alphaCutoff=src.threshold,
                doubleSided=src.double_sided,
                extensions=formats.gltf.materialsItemExtension(
                    KHR_materials_unlit=formats.gltf.
                    KHR_materials_unlitGlTFExtension()),
                extras=None)

        material_index = len(self.materials)
        self.materials.append(gltf_material)
        self.material_map[src] = material_index
        return material_index

    def _get_or_create_texture(self, src: Texture,
                               buffer: formats.BufferManager) -> int:
        texture_index = self.texture_map.get(src)
        if isinstance(texture_index, int):
            return texture_index

        logger.debug(f'add_texture: {src.name}')

        png = get_png_bytes(src)
        view_index = buffer.add_view(src.name, png)
        image_index = len(self.images)
        self.images.append(
            formats.gltf.Image(name=src.name,
                               uri=None,
                               mimeType=formats.gltf.ImageMimeType.ImagePng,
                               bufferView=view_index))

        sampler_index = len(self.samplers)
        self.samplers.append(
            formats.gltf.Sampler(
                magFilter=formats.gltf.SamplerMagFilter.NEAREST,
                minFilter=formats.gltf.SamplerMinFilter.NEAREST,
                wrapS=formats.gltf.SamplerWrapS.REPEAT,
                wrapT=formats.gltf.SamplerWrapT.REPEAT))

        dst = formats.gltf.Texture(name=src.name,
                                   source=image_index,
                                   sampler=sampler_index)

        texture_index = len(self.textures)
        self.textures.append(dst)
        return texture_index


def get_min_max3(buffer: memoryview) -> Tuple[List[float], List[float]]:
    Vector3Array = (Float3 * len(buffer))
    values = Vector3Array.from_buffer(buffer)
    min: List[float] = [float('inf')] * 3
    max: List[float] = [float('-inf')] * 3
    for v in values:
        if v.x < min[0]:
            min[0] = v.x
        if v.x > max[0]:
            max[0] = v.x
        if v.y < min[1]:
            min[1] = v.y
        if v.y > max[1]:
            max[1] = v.y
        if v.z < min[2]:
            min[2] = v.z
        if v.z > max[2]:
            max[2] = v.z
    return min, max


class GltfExporter:
    def __init__(self, export_map: ExportMap):
        self.export_map = export_map
        self.buffer = formats.BufferManager()
        self.buffers = [self.buffer]
        self.material_exporter = MaterialExporter()

        self.gltf_nodes: List[formats.gltf.Node] = []
        self.gltf_meshes: List[formats.gltf.Mesh] = []
        self.gltf_skins: List[formats.gltf.Skin] = []
        self.gltf_roots: List[int] = []
        self._mesh_index_map: Dict[Union[pyscene.SubmeshMesh,
                                         pyscene.FaceMesh], int] = {}
        self._skin_index_map: Dict[pyscene.Skin, int] = {}

    def _get_or_create_node(self, node: pyscene.Node):

        p = node.get_local_position()
        name = node.name
        if node.mesh:
            name = 'mesh.' + name

        mesh_index = self._get_or_create_mesh(node)
        skin_index = self._get_or_create_skin(node)

        gltf_node = formats.gltf.Node(name=name,
                                      children=[
                                          self.export_map.nodes.index(child)
                                          for child in node.children
                                      ],
                                      translation=[p.x, p.y, p.z],
                                      mesh=mesh_index,
                                      skin=skin_index)

        index = self.export_map.nodes.index(node)
        self.gltf_nodes[index] = gltf_node

    def _get_or_create_mesh(self, node: pyscene.Node) -> Optional[int]:
        '''
        UniVRM compatible shared attributes and targets
        '''
        if not node.mesh:
            return None
        mesh_index = self._mesh_index_map.get(node.mesh)
        if isinstance(mesh_index, int):
            return mesh_index

        if isinstance(node.mesh, pyscene.FaceMesh):
            mesh = facemesh_to_submesh(node)
        elif isinstance(node.mesh, pyscene.SubmeshMesh):
            mesh = node.mesh
        else:
            raise Exception()

        # store node
        logger.debug(mesh)

        # attributes
        attributes = {
            'POSITION':
            self.buffer.push_bytes(
                f'{mesh.name}.POSITION',
                memoryview(mesh.attributes.position),  # type: ignore
                get_min_max3),
            'NORMAL':
            self.buffer.push_bytes(
                f'{mesh.name}.NORMAL',
                memoryview(mesh.attributes.normal)),  # type: ignore
        }
        if mesh.attributes.texcoord:
            attributes['TEXCOORD_0'] = self.buffer.push_bytes(
                f'{mesh.name}.TEXCOORD_0',
                memoryview(mesh.attributes.texcoord))  # type: ignore
        if mesh.attributes.joints and mesh.attributes.weights:
            attributes['JOINTS_0'] = self.buffer.push_bytes(
                f'{mesh.name}.JOINTS_0',
                memoryview(mesh.attributes.joints))  # type: ignore
            attributes['WEIGHTS_0'] = self.buffer.push_bytes(
                f'{mesh.name}.WEIGHTS_0',
                memoryview(mesh.attributes.weights))  # type: ignore

        # morph targets
        targets = []
        # target_names = []
        # for k, v in mesh.morph_map.items():
        #     zero = (Float3 * (len(v)))()
        #     target = {
        #         'POSITION':
        #         self.buffer.push_bytes(f'{mesh.name}.targets[{k}].POSITION',
        #                                v,
        #                                get_min_max3,
        #                                use_sparse=True),
        #         'NORMAL':
        #         self.buffer.push_bytes(
        #             f'{mesh.name}.targets[{k}].NORMAL',
        #             memoryview(zero),  # type: ignore
        #             use_sparse=True)
        #     }
        #     targets.append(target)
        #     target_names.append(k)

        primitives = []
        offset = 0
        for i, submesh in enumerate(mesh.submeshes):
            # submesh indices
            indices = mesh.indices[offset:offset + submesh.vertex_count]
            offset += submesh.vertex_count
            indices_accessor_index = self.buffer.push_bytes(
                f'{mesh.name}[{i}].INDICES', memoryview(indices))

            primitive = formats.gltf.MeshPrimitive(
                attributes=attributes,
                indices=indices_accessor_index,
                material=self.material_exporter.get_or_create_material(
                    submesh.material, self.buffer),
                mode=formats.gltf.MeshPrimitiveMode.TRIANGLES,
                targets=targets,
                # gltf.MeshPrimitiveExtra(target_names)
            )
            primitives.append(primitive)

        gltf_mesh = formats.gltf.Mesh(name=mesh.name,
                                      primitives=primitives,
                                      extensions={},
                                      extras={})
        mesh_index = len(self.gltf_meshes)
        self.gltf_meshes.append(gltf_mesh)
        self._mesh_index_map[node.mesh] = mesh_index
        return mesh_index

    def _get_or_create_skin(self, node: pyscene.Node) -> Optional[int]:
        if not node.skin:
            return None

        skin_index = self._skin_index_map.get(node.skin)
        if isinstance(skin_index, int):
            return skin_index

        skin = node.skin
        # joints = [joint for joint in skin.traverse()][1:]

        matrices = (Mat4 * len(skin.joints))()
        for i, _ in enumerate(skin.joints):
            p = skin.joints[i].position
            matrices[i] = Mat4.translation(-p.x, -p.y, -p.z)
        matrix_index = self.buffer.push_bytes(
            f'{skin.name}.inverseBindMatrices',
            memoryview(matrices))  # type: ignore

        gltf_skin = formats.gltf.Skin(name=skin.name,
                                      inverseBindMatrices=matrix_index,
                                      skeleton=None,
                                      joints=[
                                          self.export_map.nodes.index(joint)
                                          for joint in skin.joints
                                      ])

        skin_index = len(self.gltf_skins)
        self.gltf_skins.append(gltf_skin)
        return skin_index

    def export_vrm(self) -> Optional[formats.generated.vrm]:
        humanoid_bones = [
            node for node in self.export_map.nodes if node.humanoid_bone
        ]
        if humanoid_bones:
            print(f'has vrm: {humanoid_bones}')
            vrm = self.export_map.vrm
            VRM = {
                'exporterVersion':
                'bl_vrm-0.1',
                'specVersion':
                '0.0',
                'meta':
                vrm.meta if vrm.meta else {},
                'humanoid': {
                    'humanBones': [{
                        'bone': node.humanoid_bone.name,
                        'node': self.export_map.nodes.index(node)
                    } for node in humanoid_bones]
                },
                'firstPerson': {},
                'blendShapeMaster': {},
                'secondaryAnimation': {
                    'boneGroups': [],
                    'colliderGroups': []
                },
                'materialProperties': [{
                    'shader': 'VRM_USE_GLTFSHADER',
                    'floatProperties': {},
                    'vectorProperties': {},
                    'textureProperties': {},
                    'keywordMap': {},
                    'tagMap': {}
                } for material in self.export_map.materials]
            }
            return formats.generated.vrm.from_dict(VRM)

    def _push_node_recursive(self, node: pyscene.Node, level=0):
        indent = '  ' * level
        self._get_or_create_node(node)
        for child in node.children:
            self._push_node_recursive(child, level + 1)

    def export(self) -> Tuple[formats.gltf.glTF, List[formats.BufferManager]]:
        # 情報を蓄える
        self.gltf_nodes = [None] * len(self.export_map.nodes)
        for node in self.export_map.nodes:
            if not node.parent:
                self._push_node_recursive(node)
                self.gltf_roots.append(self.export_map.nodes.index(node))

        # extensions
        extensionsUsed = ['KHR_materials_unlit']
        vrm = self.export_vrm()
        extensions = {}
        if vrm:
            extensions['VRM'] = vrm.to_dict()
            extensionsUsed.append('VRM')

        # 出力する
        data = formats.gltf.glTF(
            asset=formats.gltf.Asset(generator=GENERATOR_NAME,
                                     version=GLTF_VERSION),
            buffers=[
                formats.gltf.Buffer(byteLength=len(self.buffer.buffer.data))
            ],
            bufferViews=self.buffer.views,
            accessors=self.buffer.accessors,
            images=self.material_exporter.images,
            samplers=self.material_exporter.samplers,
            textures=self.material_exporter.textures,
            materials=self.material_exporter.materials,
            nodes=self.gltf_nodes,
            meshes=self.gltf_meshes,
            skins=self.gltf_skins,
            scenes=[formats.gltf.Scene(name='main', nodes=self.gltf_roots)],
            extensionsUsed=extensionsUsed,
            extensions=extensions)
        return data, self.buffers


def to_gltf(export_map: ExportMap) -> formats.GltfContext:
    exporter = GltfExporter(export_map)
    exported, bins = exporter.export()
    return formats.GltfContext(exported, bytes(bins[0].buffer.data),
                               pathlib.Path())
