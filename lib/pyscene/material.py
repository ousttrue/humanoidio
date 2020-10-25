from logging import getLogger
logger = getLogger(__name__)
from typing import Optional, List, Dict, Union
import pathlib
from enum import Enum
#
import bpy
from ..formats import gltf
from ..formats.buffermanager import BufferManager
from ..struct_types import Float4


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


class TextureUsage(Enum):
    Unknown = 0
    Color = 1
    NormalMap = 2
    EmissiveTexture = 3
    OcclusionTexture = 4
    MetallicRoughnessTexture = 5


class Texture:
    def __init__(self, name: str, url_or_bytes: Union[pathlib.Path, bytes]):
        self.name = name
        self.url_or_bytes = url_or_bytes
        self.usage = TextureUsage.Unknown
        self.is_data = False

    def __str__(self) -> str:
        return f'<[{self.usage}] {self.name}>'

    def set_usage(self, usage: TextureUsage):
        if self.usage != TextureUsage.Unknown and self.usage != usage:
            raise Exception('multi use by different usage')
        self.usage = usage
        if usage in [
                TextureUsage.Color,
                TextureUsage.EmissiveTexture,
        ]:
            self.is_data = False
        else:
            self.is_data = True


class BlendMode(Enum):
    Opaque = 1
    AlphaBlend = 2
    Mask = 3


class Material:
    '''
    unlit
    '''
    def __init__(self, name: str):
        self.name = name
        self.color = Float4(1, 1, 1, 1)
        self.texture: Optional[Texture] = None
        self.blend_mode: BlendMode = BlendMode.Opaque
        self.threshold = 0.5
        self.double_sided = False

    def __str__(self):
        return f'<Unlit {self.name}>'


class PBRMaterial(Material):
    '''
    PBR
    '''
    def __init__(self, name: str):
        super().__init__(name)
        self.metallic = 0.0
        self.roughness = 0.0  # 1 - smoothness
        self.normal_map: Optional[Texture] = None
        self.emissive_texture: Optional[Texture] = None
        self.metallic_roughness_texture: Optional[Texture] = None
        self.occlusion_texture: Optional[Texture] = None

    def __str__(self):
        return f'<PBR {self.name}>'


class MaterialStore:
    def __init__(self):
        self.images: List[gltf.Image] = []
        self.samplers: List[gltf.Sampler] = []
        self.textures: List[gltf.Texture] = []
        self.texture_map: Dict[bpy.types.Image, int] = {}
        self.materials: List[gltf.Material] = []
        self.material_map: Dict[bpy.types.Material, int] = {}

    def get_texture_index(self, texture: bpy.types.Image,
                          buffer: BufferManager) -> int:
        if texture in self.texture_map:
            return self.texture_map[texture]

        gltf_texture_index = len(self.textures)
        self.texture_map[texture] = gltf_texture_index
        self.add_texture(texture, buffer)
        return gltf_texture_index

    def add_texture(self, src: bpy.types.Image, buffer: BufferManager):
        image_index = len(self.images)

        logger.debug(f'add_texture: {src.name}')
        png = image_to_png(src)
        view_index = buffer.add_view(src.name, png)

        self.images.append(
            gltf.Image(name=src.name,
                       uri=None,
                       mimeType=gltf.MimeType.Png,
                       bufferView=view_index))

        sampler_index = len(self.samplers)
        self.samplers.append(
            gltf.Sampler(magFilter=gltf.MagFilterType.NEAREST,
                         minFilter=gltf.MinFilterType.NEAREST,
                         wrapS=gltf.WrapMode.REPEAT,
                         wrapT=gltf.WrapMode.REPEAT))

        dst = gltf.Texture(name=src.name,
                           source=image_index,
                           sampler=sampler_index)
        self.textures.append(dst)

    def get_material_index(self, material: bpy.types.Material,
                           bufferManager: BufferManager) -> int:
        if material in self.material_map:
            return self.material_map[material]

        gltf_material_index = len(self.materials)
        self.material_map[material] = gltf_material_index
        if material:
            self.add_material(material, bufferManager)
        else:
            self.materials.append(gltf.create_default_material())
        return gltf_material_index

    def add_material(self, src: bpy.types.Material,
                     bufferManager: BufferManager):
        # texture
        color_texture = None
        normal_texture = None
        alpha_mode = gltf.MaterialAlphaMode.OPAQUE

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

        dst = gltf.Material(
            name=src.name,
            pbrMetallicRoughness=gltf.MaterialPBRMetallicRoughness(
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
            extensions=gltf.materialsItemExtension(
                KHR_materials_unlit=gltf.KHR_materials_unlitGlTFExtension()),
            extras=None)
        self.materials.append(dst)
