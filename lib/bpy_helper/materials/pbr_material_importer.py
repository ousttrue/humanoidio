from typing import Callable
import bpy
from .. import pyscene
from . import wrap_node


def build_pbr(bl_material: bpy.types.Material, src: pyscene.UnlitMaterial,
              get_or_create_image: Callable[[pyscene.Texture],
                                            bpy.types.Image]):
    '''
    BsdfPrincipled
    '''
    factory = wrap_node.WrapNodeFactory(bl_material)

    # build node
    output = factory.create('OutputMaterial')
    bsdf = factory.create('BsdfPrincipled', -300, 0)
    # bsdf_node.set_default_value(
    #     'Base Color', (src.color.x, src.color.y, src.color.z, src.color.w))
    output.connect('Surface', bsdf)

    color = factory.create('MixRGB', -500)
    color.node.blend_type = 'MULTIPLY'
    color.set_default_value('Fac', 1)
    color.set_default_value('Color1',
                            (src.color[0], src.color[1], src.color[2], 1))
    bsdf.connect('Base Color', color)

    if src.color_texture:
        # color texture
        color_texture = factory.create('TexImage', -700)
        color_texture.node.image = get_or_create_image(src.color_texture)
        color.connect('Color2', color_texture, 'Color')

    # if src.normal_texture:
    #     # normal map
    #     normal_texture_node = self._create_node('TexImage')
    #     normal_texture_node.label = 'NormalTexture'
    #     normal_image = get_or_create_image(src.normal_texture)  # type: ignore
    #     normal_texture_node.image = normal_image

    #     normal_map = self._create_node('NormalMap')
    #     self.links.new(normal_texture_node.outputs[0],
    #                    normal_map.inputs[1])  # type: ignore
    #     self.links.new(normal_map.outputs[0],
    #                    bsdf_node.inputs['Normal'])  # type: ignore

    # if src.emissive_texture:
    #     self._create_texture_node('EmissiveTexture',
    #                               get_or_create_image(src.emissive_texture),
    #                               False, bsdf_node.inputs['Emission'], None)

    # if src.metallic_roughness_texture:
    #     separate_node = self._create_node('SeparateRGB')
    #     self.links.new(separate_node.outputs['G'],
    #                    bsdf_node.inputs['Roughness'])  # type: ignore
    #     self.links.new(separate_node.outputs['B'],
    #                    bsdf_node.inputs['Metallic'])  # type: ignore
    #     self._create_texture_node(
    #         'MetallicRoughness',
    #         get_or_create_image(src.metallic_roughness_texture), False,
    #         separate_node.inputs[0], None)

    # if src.occlusion_texture:
    #     pass
