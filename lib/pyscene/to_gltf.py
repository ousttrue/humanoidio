'''
* serialize: pyscene => GLTF
* deserialize: GLTF => pyscene
'''
import pathlib
from logging import getLogger
logger = getLogger(__name__)
from typing import List, Optional, Tuple, Any, Iterator, Dict
import bpy, mathutils
from .. import formats
from ..struct_types import Float3, Mat4
from .submesh_mesh import SubmeshMesh
from .facemesh import FaceMesh
from .to_submesh import facemesh_to_submesh
from .node import Node, Skin

GLTF_VERSION = '2.0'
GENERATOR_NAME = 'pyimpex'


def image_to_png(image: bpy.types.Image) -> bytes:
    '''
    https://blender.stackexchange.com/questions/62072/does-blender-have-a-method-to-a-get-png-formatted-bytearray-for-an-image-via-pyt
    '''
    import struct
    import zlib

    width = image.size[0]
    height = image.size[1]
    buf = bytearray([int(p * 255) for p in image.pixels])

    # reverse the vertical line order and add null bytes at the start
    width_byte_4 = width * 4
    raw_data = b''.join(b'\x00' + buf[span:span + width_byte_4]
                        for span in range((height - 1) *
                                          width_byte_4, -1, -width_byte_4))

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return (struct.pack("!I", len(data)) + chunk_head +
                struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))

    png_bytes = b''.join([
        b'\x89PNG\r\n\x1a\n',
        png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, 6, 0, 0, 0)),
        png_pack(b'IDAT', zlib.compress(raw_data, 9)),
        png_pack(b'IEND', b'')
    ])
    return png_bytes


class MaterialExporter:
    def __init__(self):
        self.images: List[formats.gltf.Image] = []
        self.samplers: List[formats.gltf.Sampler] = []
        self.textures: List[formats.gltf.Texture] = []
        self.materials: List[formats.gltf.Material] = []
        self.texture_map: Dict[bpy.types.Image, int] = {}
        self.material_map: Dict[bpy.types.Material, int] = {}

    def get_texture_index(self, texture: bpy.types.Image,
                          buffer: formats.BufferManager) -> int:
        if texture in self.texture_map:
            return self.texture_map[texture]

        gltf_texture_index = len(self.textures)
        self.texture_map[texture] = gltf_texture_index
        self.add_texture(texture, buffer)
        return gltf_texture_index

    def add_texture(self, src: bpy.types.Image, buffer: formats.BufferManager):
        image_index = len(self.images)

        logger.debug(f'add_texture: {src.name}')
        png = image_to_png(src)
        view_index = buffer.add_view(src.name, png)

        self.images.append(
            formats.gltf.Image(name=src.name,
                       uri=None,
                       mimeType=formats.gltf.MimeType.Png,
                       bufferView=view_index))

        sampler_index = len(self.samplers)
        self.samplers.append(
            formats.gltf.Sampler(magFilter=formats.gltf.MagFilterType.NEAREST,
                         minFilter=formats.gltf.MinFilterType.NEAREST,
                         wrapS=formats.gltf.WrapMode.REPEAT,
                         wrapT=formats.gltf.WrapMode.REPEAT))

        dst = formats.gltf.Texture(name=src.name,
                           source=image_index,
                           sampler=sampler_index)
        self.textures.append(dst)

    def get_material_index(self, material: bpy.types.Material,
                           bufferManager: formats.BufferManager) -> int:
        if material in self.material_map:
            return self.material_map[material]

        gltf_material_index = len(self.materials)
        self.material_map[material] = gltf_material_index
        if material:
            self.add_material(material, bufferManager)
        else:
            self.materials.append(formats.gltf.create_default_material())
        return gltf_material_index

    def add_material(self, src: bpy.types.Material,
                     bufferManager: formats.BufferManager):
        # texture
        color_texture = None
        normal_texture = None
        alpha_mode = formats.gltf.MaterialAlphaMode.OPAQUE

        # if slot.use_map_color_diffuse and slot.texture and slot.texture.image:
        #     color_texture_index = self.get_texture_index(
        #         slot.texture.image, bufferManager)
        #     color_texture = gltf.TextureInfo(
        #         index=color_texture_index,
        #         texCoord=0
        #     )
        #     if slot.use_map_alpha:
        #         if slot.use_stencil:
        #             alpha_mode = gltf.AlphaMode.MASK
        #         else:
        #             alpha_mode = gltf.AlphaMode.BLEND
        # elif slot.use_map_normal and slot.texture and slot.texture.image:
        #     normal_texture_index = self.get_texture_index(
        #         slot.texture.image, bufferManager)
        #     normal_texture = gltf.MaterialNormalTextureInfo(
        #         index=normal_texture_index,
        #         texCoord=0,
        #         scale=slot.normal_factor,
        #     )

        # material
        color = [0.5, 0.5, 0.5, 1.0]
        texture = None
        # if src.use_nodes:
        #     principled_bsdf = src.node_tree.nodes['Principled BSDF']
        #     if principled_bsdf:

        #         base_color = principled_bsdf.inputs["Base Color"]

        #         if base_color.is_linked:
        #             from_node = base_color.links[0].from_node
        #             if from_node.bl_idname == 'ShaderNodeTexImage':
        #                 image = from_node.image
        #                 if image:
        #                     color_texture_index = self.get_texture_index(
        #                         image, bufferManager)
        #                     color_texture = gltf.TextureInfo(
        #                         index=color_texture_index, texCoord=0)

        #         else:
        #             color = [x for x in base_color.default_value]

        # else:
        #     color = [x for x in src.diffuse_color]

        dst = formats.gltf.Material(
            name=src.name,
            pbrMetallicRoughness=formats.gltf.MaterialPBRMetallicRoughness(
                baseColorFactor=color,
                baseColorTexture=color_texture,
                metallicFactor=0,
                roughnessFactor=0.9,
                metallicRoughnessTexture=None,
                extensions={},
                extras={}),
            normalTexture=normal_texture,
            occlusionTexture=None,
            emissiveTexture=None,
            emissiveFactor=None,
            alphaMode=alpha_mode,
            alphaCutoff=None,
            doubleSided=False,
            extensions=formats.gltf.materialsItemExtension(
                KHR_materials_unlit=formats.gltf.KHR_materials_unlitGlTFExtension()),
            extras=None)
        self.materials.append(dst)


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
    def __init__(self):
        self.buffer = formats.BufferManager()
        self.buffers = [self.buffer]
        self.meshes: List[formats.gltf.Mesh] = []
        self.skins: List[formats.gltf.Skin] = []
        self.nodes: List[formats.gltf.Node] = []
        self.roots: List[int] = []
        self.material_exporter = MaterialExporter()

    def _to_gltf_mesh(self, mesh: SubmeshMesh) -> formats.gltf.Mesh:
        '''
        UniVRM compatible shared attributes and targets
        '''
        # attributes
        attributes = {
            'POSITION':
            self.buffer.push_bytes(f'{mesh.name}.POSITION',
                                   memoryview(mesh.attributes.position),
                                   get_min_max3),
            'NORMAL':
            self.buffer.push_bytes(f'{mesh.name}.NORMAL',
                                   memoryview(mesh.attributes.normal)),
        }
        if mesh.attributes.texcoord:
            attributes['TEXCOORD_0'] = self.buffer.push_bytes(
                f'{mesh.name}.TEXCOORD_0',
                memoryview(mesh.attributes.texcoord))
        if mesh.attributes.joints and mesh.attributes.weights:
            attributes['JOINTS_0'] = self.buffer.push_bytes(
                f'{mesh.name}.JOINTS_0', memoryview(mesh.attributes.joints))
            attributes['WEIGHTS_0'] = self.buffer.push_bytes(
                f'{mesh.name}.WEIGHTS_0', memoryview(mesh.attributes.weights))

        # morph targets
        targets = []
        target_names = []
        for k, v in mesh.morph_map.items():
            zero = (Float3 * (len(v)))()
            target = {
                'POSITION':
                self.buffer.push_bytes(f'{mesh.name}.targets[{k}].POSITION',
                                       v,
                                       get_min_max3,
                                       use_sparse=True),
                'NORMAL':
                self.buffer.push_bytes(f'{mesh.name}.targets[{k}].NORMAL',
                                       memoryview(zero),
                                       use_sparse=True)
            }
            targets.append(target)
            target_names.append(k)

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
                material=0,
                mode=formats.gltf.MeshPrimitiveMode.TRIANGLES,
                targets=targets,
                # gltf.MeshPrimitiveExtra(target_names)
            )
            primitives.append(primitive)

        return formats.gltf.Mesh(name=mesh.name,
                                 primitives=primitives,
                                 extensions={},
                                 extras={})

    def _to_gltf_node(self, node: Node) -> formats.gltf.Node:
        # store node
        # if isinstance(node.mesh, pyscene.FaceMesh):
        #     submesh_mesh = facemesh_to_submesh(node)
        #     logger.debug(submesh_mesh)
        #     self.meshes.append(self._to_gltf_mesh(submesh_mesh))

        p = node.get_local_position()
        name = node.name
        if node.mesh:
            name = 'mesh.' + name
        return formats.gltf.Node(
            name=name,
            children=[nodes.index(child) for child in node.children],
            translation=(p.x, p.y, p.z),
            mesh=meshes.index(node.mesh) if node.mesh else None
            # skin=skins.index(node.skin) if node.skin else None
        )

    def _to_gltf_skin(self, skin: Node, nodes: List[Node]):
        joints = [joint for joint in skin.traverse()][1:]

        matrices = (Mat4 * len(joints))()
        for i, _ in enumerate(joints):
            p = joints[i].position
            matrices[i] = Mat4.translation(-p.x, -p.y, -p.z)
        matrix_index = self.buffer.push_bytes(
            f'{skin.name}.inverseBindMatrices',
            memoryview(matrices))  # type: ignore

        return formats.gltf.Skin(
            name=skin.name,
            inverseBindMatrices=matrix_index,
            skeleton=nodes.index(skin),
            joints=[nodes.index(joint) for joint in joints])

    def _export_vrm(self, nodes: List[Node], version: str, title: str,
                    author: str):
        humanoid_bones = [node for node in nodes if node.humanoid_bone]
        if humanoid_bones:
            meta = {
                'version': version,
                'title': title,
                'author': author,
                'contactInformation': '',
                'reference': '',
                'texture': -1,
                'allowedUserName': 'OnlyAuthor',
                'violentUssageName': 'Disallow',
                'sexualUssageName': 'Disallow',
                'commercialUssageName': 'Disallow',
                'otherPermissionUrl': '',
                'licenseName': 'Redistribution_Prohibited',
                'otherLicenseUrl': '',
            }
            VRM = {
                'exporterVersion':
                'bl_vrm-0.1',
                'specVersion':
                '0.0',
                'meta':
                meta,
                'humanoid': {
                    'humanBones': [{
                        'bone': node.humanoid_bone.name,
                        'node': nodes.index(node)
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
                } for material in self.material_exporter.materials]
            }
            return VRM

    def _push_node_recursive(self, node: Node):
        gltf_node = self._to_gltf_node(node)
        self.nodes.append(gltf_node)

        for child in node.children:
            self._push_node_recursive(child)

    def push_tree(self, root: Node):
        '''
        情報を蓄える
        '''
        self._push_node_recursive(root)

    def export(self) -> Tuple[formats.gltf.glTF, List[formats.BufferManager]]:
        '''
        出力する
        '''

        extensionsUsed = ['KHR_materials_unlit']

        # vrm = self.export_vrm(nodes, scanner.vrm.version,
        #                       scanner.vrm.title, scanner.vrm.author)
        # if vrm:
        #     extensionsUsed.append('VRM')

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
            nodes=self.nodes,
            meshes=self.meshes,
            skins=self.skins,
            scenes=[formats.gltf.Scene(name='main', nodes=self.roots)],
            extensionsUsed=extensionsUsed,
            # extensions={'VRM': vrm}
        )

        return data, self.buffers


def to_gltf(nodes: List[Node]) -> formats.GltfContext:
    exporter = GltfExporter()
    for node in nodes:
        if not node.parent:
            exporter.push_tree(node)

    exported, bins = exporter.export()
    return formats.GltfContext(exported, bytes(bins[0].buffer.data),
                               pathlib.Path())
