from logging import getLogger
logger = getLogger(__name__)
import bpy
from .. import pyscene
from .wrap_node import WrapNode, WrapNodeFactory
from .texture_importer import TextureImporter

GROUP_NAME = 'pyimpex_Unlit'


def get_or_unlit_group() -> bpy.types.NodeTree:
    '''
    Unlit
    '''
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
    g.inputs.new('NodeSocketColor',
                 'ColorTexture').default_value = (1, 1, 1, 1)
    g.inputs.new('NodeSocketFloat', 'Alpha').default_value = 1
    input = WrapNode(g.links, group_inputs)

    multiply = factory.create('MixRGB', -600)
    multiply.node.blend_type = 'MULTIPLY'  # type: ignore
    multiply.set_default_value('Fac', 1)
    multiply.connect('Color1', input, 'Color')
    multiply.connect('Color2', input, 'ColorTexture')

    emission = factory.create('Emission', -400)
    emission.connect('Color', multiply)

    transparent = factory.create('BsdfTransparent', -400, 200)

    mix = factory.create('MixShader', -200)
    mix.connect('Fac', input, 'Alpha')
    mix.connect(1, transparent)
    mix.connect(2, emission)

    # create group outputs
    group_outputs = g.nodes.new('NodeGroupOutput')
    g.outputs.new('NodeSocketFloat', 'Surface')
    output = WrapNode(g.links, group_outputs)
    output.connect('Surface', mix)

    return g


def build(bl_material: bpy.types.Material, src: pyscene.UnlitMaterial,
                texture_importer: TextureImporter):
    '''
    out -> mix Fac-> alpha ------------>|
               Sahder1 -> transparent   | TexImage
               Shader2 -> color ------->|
    '''
    factory = WrapNodeFactory(bl_material.node_tree)

    g = factory.create('Group', -300)
    g.node.node_tree = get_or_unlit_group()
    g.set_default_value('Color', (src.color[0], src.color[1], src.color[2], 1))
    g.set_default_value('Alpha', src.color[3])
    if src.color_texture:
        color_texture = factory.create('TexImage', -600, -100)
        color_texture.set_image(
            texture_importer.get_or_create_image(src.color_texture))
        g.connect('ColorTexture', color_texture, 'Color')
        g.connect('Fac', color_texture, 'Alpha')

    out = factory.create('OutputMaterial')
    out.connect('Surface', g)
