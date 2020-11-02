from logging import getLogger
logger = getLogger(__name__)
import bpy
from .. import pyscene
from .texture_importer import TextureImporter
from .wrap_node import WrapNode, WrapNodeFactory

GROUP_NAME = 'pyimpex:MToon'


def _get_or_create_group() -> bpy.types.NodeTree:
    g = bpy.data.node_groups.get(GROUP_NAME)
    if g:
        return g

    logger.debug(f'node group: {GROUP_NAME}')
    g = bpy.data.node_groups.new(GROUP_NAME, type='ShaderNodeTree')
    factory = WrapNodeFactory(g)

    # create group inputs
    group_inputs = g.nodes.new('NodeGroupInput')
    group_inputs.location = (-900, 0)
    g.inputs.new('NodeSocketColor', 'Color').default_value = (1, 1, 1, 1)
    g.inputs.new('NodeSocketColor', 'ShadeColor').default_value = (1, 1, 1, 1)
    g.inputs.new('NodeSocketColor',
                 'ColorTexture').default_value = (1, 1, 1, 1)
    g.inputs.new('NodeSocketFloat', 'Alpha').default_value = 1
    g.inputs.new('NodeSocketColor',
                 'NormalTexture').default_value = (0.5, 0.5, 1, 1)
    g.inputs.new('NodeSocketFloat', 'NormalStrength').default_value = 1
    input = WrapNode(g.links, group_inputs)

    multiply = factory.create('MixRGB', -600)
    multiply.node.blend_type = 'MULTIPLY'  # type: ignore
    multiply.set_default_value('Fac', 1)
    multiply.connect('Color1', input, 'Color')
    multiply.connect('Color2', input, 'ColorTexture')

    normal_map = factory.create('NormalMap', -600, -500)
    normal_map.connect('Strength', input, 'NormalStrength')

    bsdf = factory.create('BsdfPrincipled', -300)
    bsdf.set_default_value('Metallic', 0)
    bsdf.set_default_value('Roughness', 1)
    bsdf.connect('Base Color', multiply)
    bsdf.connect('Alpha', input, 'Alpha')
    bsdf.connect('Normal', normal_map)

    # create group outputs
    group_outputs = g.nodes.new('NodeGroupOutput')
    g.outputs.new('NodeSocketFloat', 'Surface')
    output = WrapNode(g.links, group_outputs)
    output.connect('Surface', bsdf)

    return g


def build(bl_material: bpy.types.Material, src: pyscene.MToonMaterial,
          texture_importer: TextureImporter):
    '''
    BsdfPrincipled
    '''
    factory = WrapNodeFactory(bl_material.node_tree)

    g = factory.create('Group', -300)
    g.node.node_tree = _get_or_create_group()
    g.set_default_value(
        'ShadeColor',
        (src.shade_color.x, src.shade_color.y, src.shade_color.z, 1))

    out = factory.create('OutputMaterial')
    out.connect('Surface', g)

    # #
    # # color ramp
    # # bsdf -> to_rgb -> ramp -> ramp_mult -> from_rgb -> output
    # #
    # to_rgb = factory.create('ShaderToRGB')
    # to_rgb.connect('Shader', bsdf)

    # ramp = factory.create('ValToRGB', 200)
    # ramp.node.label = 'ShadeColor'
    # ramp.connect('Fac', to_rgb)
    # color_ramp: bpy.types.ColorRamp = ramp.node.color_ramp  # type: ignore
    # if len(color_ramp.elements) != 2:
    #     raise Exception()
    # color_ramp.elements[0].position = 0.5
    # color_ramp.elements[1].position = 0.5
    # color_ramp.elements[0].color = (src.shade_color.x, src.shade_color.y,
    #                                 src.shade_color.z, 1)

    # ramp_mult = factory.create('MixRGB', 500)
    # ramp_mult.node.blend_type = 'MULTIPLY'  # type: ignore
    # ramp_mult.set_default_value('Fac', 1)
    # ramp_mult.connect('Color1', ramp)

    # from_rgb = factory.create('Emission', 500, -200)
    # from_rgb.connect('Color', ramp_mult)

    # output = factory.create('OutputMaterial', 500, -400)
    # output.connect('Surface', from_rgb)

    # color = factory.create('MixRGB', -500)
    # color.node.blend_type = 'MULTIPLY'  # type: ignore
    # color.set_default_value('Fac', 1)
    # color.set_default_value('Color1',
    #                         (src.color[0], src.color[1], src.color[2], 1))
    # ramp_mult.connect('Color2', color)
    if src.color_texture:
        # color texture
        color_texture = factory.create('TexImage', -600)
        color_texture.node.label = 'BaseColorTexture'
        color_texture.set_image(
            texture_importer.get_or_create_image(src.color_texture))
        g.connect('ColorTexture', color_texture, 'Color')
        g.connect('Alpha', color_texture, 'Alpha')

    # # emissive
    # emissive = factory.create('MixRGB', -500, -600)
    # emissive.node.blend_type = 'MULTIPLY'  # type: ignore
    # emissive.set_default_value('Fac', 1)
    # emissive.set_default_value('Color1',
    #                            (src.emissive_color[0], src.emissive_color[1],
    #                             src.emissive_color[2], 1))
    # bsdf.connect('Emission', emissive)
    # if src.emissive_texture:
    #     emissive_texture = factory.create('TexImage', -800, -600)
    #     emissive_texture.node.label = 'EmissiveTexture'
    #     emissive_texture.set_image(
    #         texture_importer.get_or_create_image(src.emissive_texture))
    #     emissive.connect('Color2', emissive_texture, 'Color')

    # normal map
    if src.normal_texture:
        normal_texture = factory.create('TexImage', -600, -300)
        normal_texture.node.label = 'NormalTexture'
        normal_texture.set_image(
            texture_importer.get_or_create_image(src.normal_texture))
        g.connect('NormalTexture', normal_texture, 'Color')

    # # ToDo:
    # # if src.occlusion_texture:
    # #     pass
