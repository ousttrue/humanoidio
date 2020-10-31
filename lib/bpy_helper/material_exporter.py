from typing import List, Dict
import pathlib
import bpy
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from .. import pyscene
from ..struct_types import Float4

# material
# texture = None
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

# texture
# color_texture = src.texture
# normal_texture = src.normal_map
# alpha_mode = formats.gltf.MaterialAlphaMode.OPAQUE

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

# def
# '''
# https://blender.stackexchange.com/questions/62072/does-blender-have-a-method-to-a-get-png-formatted-bytearray-for-an-image-via-pyt
# '''
# import struct
# import zlib
#
# width = image.size[0]
# height = image.size[1]
# buf = bytes([int(p * 255) for p in image.pixels])  # type: ignore

# # reverse the vertical line order and add null bytes at the start
# width_byte_4 = width * 4
# raw_data = b''.join(b'\x00' + buf[span:span + width_byte_4]
#                     for span in range((height - 1) *
#                                       width_byte_4, -1, -width_byte_4))

# def png_pack(png_tag, data):
#     chunk_head = png_tag + data
#     return (struct.pack("!I", len(data)) + chunk_head +
#             struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))

# png_bytes = b''.join([
#     b'\x89PNG\r\n\x1a\n',
#     png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, 6, 0, 0, 0)),
#     png_pack(b'IDAT', zlib.compress(raw_data, 9)),
#     png_pack(b'IEND', b'')
# ])
# return png_bytes


class MaterialExporter:
    def __init__(self):
        self.materials: List[pyscene.UnlitMaterial] = []
        self._material_map: Dict[bpy.types.Material, int] = {}

    def get_or_create_material(self,
                               m: bpy.types.Material) -> pyscene.UnlitMaterial:
        material_index = self._material_map.get(m)
        if isinstance(material_index, int):
            return self.materials[material_index]

        nodes = m.node_tree.nodes
        links = m.node_tree.links

        has_principled_bsdf = None
        for n in nodes:
            if isinstance(n, bpy.types.ShaderNodeBsdfPrincipled):
                has_principled_bsdf = n
                break

        if has_principled_bsdf:
            material = pyscene.PBRMaterial(m.name)
            # color
            # colorTexture

            # Export
            principled = PrincipledBSDFWrapper(m, is_readonly=True)
            material.color = Float4(principled.base_color.r,
                                    principled.base_color.g,
                                    principled.base_color.b, 1.0)
            if principled.base_color_texture:
                texture: bpy.types.ShaderNodeTexImage = principled.base_color_texture               
                if texture.image:
                    image = texture.image                                
                    if image.packed_file:
                        material.color_texture = pyscene.Texture(image.name,
                                                image.packed_file.data)
                        material.color_texture.usage = pyscene.TextureUsage.Color
                    elif image.filepath:
                        material.color_texture = pyscene.Texture(image.name,
                                                pathlib.Path(image.filepath))
                        material.color_texture.usage = pyscene.TextureUsage.Color
                    else:
                        raise NotImplementedError()
        else:
            material = pyscene.UnlitMaterial(m.name)
            # color
            # colorTexture

        material_index = len(self.materials)
        self.materials.append(material)
        self._material_map[m] = material_index
        return material
