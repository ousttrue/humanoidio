from logging import getLogger
from math import radians
import mathutils
logger = getLogger(__name__)
import bpy
from .. import pyscene
from .texture_importer import TextureImporter
from .wrap_node import WrapNode, WrapNodeFactory

GROUP_NAME = 'pyimpex:MToon'


def _get_or_create_group() -> bpy.types.NodeTree:
    '''
    normal -> bsdf -> to_rgb -> ramp -> mix -> mult -> out
                                         shade   color
    '''
    g = bpy.data.node_groups.get(GROUP_NAME)
    if g:
        return g

    logger.debug(f'node group: {GROUP_NAME}')
    g = bpy.data.node_groups.new(GROUP_NAME, type='ShaderNodeTree')
    factory = WrapNodeFactory(g)

    #
    # inputs
    #
    group_inputs = g.nodes.new('NodeGroupInput')
    group_inputs.select = False
    group_inputs.location = (-900, 0)
    # color shade
    g.inputs.new('NodeSocketFloat', 'Alpha').default_value = 1
    g.inputs.new('NodeSocketColor', 'Color').default_value = (1, 1, 1, 1)
    g.inputs.new('NodeSocketColor',
                 'ColorTexture').default_value = (1, 1, 1, 1)
    # shade toon
    g.inputs.new('NodeSocketColor', 'ShadeColor').default_value = (1, 1, 1, 1)
    g.inputs.new('NodeSocketColor',
                 'ShadeColorTexture').default_value = (1, 1, 1, 1)
    g.inputs.new('NodeSocketFloat', 'ShadeToony').default_value = 0.9
    g.inputs.new('NodeSocketFloat', 'ShadingShift').default_value = 0
    # emission
    g.inputs.new('NodeSocketColor', 'Emission').default_value = (0, 0, 0, 1)
    g.inputs.new('NodeSocketColor',
                 'EmissiveTexture').default_value = (1, 1, 1, 1)

    # normal
    g.inputs.new('NodeSocketColor',
                 'NormalTexture').default_value = (0.5, 0.5, 1, 1)
    g.inputs.new('NodeSocketFloat', 'NormalStrength').default_value = 1
    g.inputs.new('NodeSocketColor',
                 'MatcapTexture').default_value = (0, 0, 0, 0)
    input = WrapNode(g.links, group_inputs)

    #
    # shading
    #
    normal_map = factory.create('NormalMap', -600, -500)
    normal_map.connect('Color', input, 'NormalTexture')
    normal_map.connect('Strength', input, 'NormalStrength')

    bsdf = factory.create('BsdfPrincipled', -300)
    bsdf.set_default_value('Metallic', 0)
    bsdf.set_default_value('Roughness', 1)
    bsdf.connect('Normal', normal_map)

    # color x color_texture
    mult_color = factory.create('MixRGB', -600)
    mult_color.node.blend_type = 'MULTIPLY'  # type: ignore
    mult_color.set_default_value('Fac', 1)
    mult_color.connect('Color1', input, 'Color')
    mult_color.connect('Color2', input, 'ColorTexture')

    #
    # toon
    #
    to_rgb = factory.create('ShaderToRGB', 0, -900)
    to_rgb.connect('Shader', bsdf)

    # toon shading
    ramp = factory.create('ValToRGB', 0, -600)
    ramp.connect('Fac', to_rgb)
    color_ramp: bpy.types.ColorRamp = ramp.node.color_ramp  # type: ignore
    # color_ramp.interpolation = 'CONSTANT'
    if len(color_ramp.elements) != 2:
        raise Exception()
    # ToDo: ShadeToony, ShadingShift
    color_ramp.elements[0].position = 0.4
    color_ramp.elements[1].position = 0.6

    ramp_mix = factory.create('MixRGB', 0, -400)
    ramp_mix.connect('Fac', ramp)
    ramp_mix.connect('Color1', input, 'ShadeColor')
    ramp_mix.set_default_value('Color2', (1, 1, 1, 1))

    # color x shade
    mult_shade = factory.create('MixRGB', 0, -200)
    mult_shade.node.blend_type = 'MULTIPLY'  # type: ignore
    mult_shade.set_default_value('Fac', 1)
    mult_shade.connect('Color1', mult_color)
    mult_shade.connect('Color2', ramp_mix)

    emission = factory.create('Emission')
    emission.connect('Color', mult_shade)

    transparent = factory.create('BsdfTransparent', -400, 100)

    mix = factory.create('MixShader', -200, 200)
    mix.connect('Fac', input, 'Alpha')
    mix.connect(1, transparent)
    mix.connect(2, emission)

    # create group outputs
    group_outputs = g.nodes.new('NodeGroupOutput')
    group_outputs.select = False
    group_outputs.location = (0, 200)
    g.outputs.new('NodeSocketFloat', 'Surface')
    output = WrapNode(g.links, group_outputs)
    output.connect('Surface', mix)

    return g


def build(bl_material: bpy.types.Material, src: pyscene.MToonMaterial,
          texture_importer: TextureImporter):
    '''
    BsdfPrincipled
    '''
    factory = WrapNodeFactory(bl_material.node_tree)

    g = factory.create('Group', -300)
    g.node.node_tree = _get_or_create_group()
    g.set_default_value('Color', (src.color.x, src.color.y, src.color.z, 1))
    g.set_default_value(
        'ShadeColor',
        (src.shade_color.x, src.shade_color.y, src.shade_color.z, 1))
    g.set_default_value('ShadeToony', src.shade_toony)
    g.set_default_value('ShadingShift', src.shading_shift)
    out = factory.create('OutputMaterial')
    out.connect('Surface', g)

    if src.color_texture:
        color_texture = factory.create('TexImage', -600)
        color_texture.node.label = 'BaseColorTexture'
        color_texture.set_image(
            texture_importer.get_or_create_image(src.color_texture))
        g.connect('ColorTexture', color_texture, 'Color')
        g.connect('Alpha', color_texture, 'Alpha')

    if src.shade_texture:
        shade_texture = factory.create('TexImage', -600, -300)
        shade_texture.node.label = 'ShadeColorTexture'
        shade_texture.set_image(
            texture_importer.get_or_create_image(src.shade_texture))
        g.connect('ShadeColorTexture', shade_texture, 'Color')

    if src.emissive_texture:
        emissive_texture = factory.create('TexImage', -600, -600)
        emissive_texture.node.label = 'EmissiveTexture'
        emissive_texture.set_image(
            texture_importer.get_or_create_image(src.emissive_texture))
        g.connect('EmissiveTexture', emissive_texture, 'Color')

    if src.normal_texture:
        normal_texture = factory.create('TexImage', -600, -900)
        normal_texture.node.label = 'NormalTexture'
        normal_texture.set_image(
            texture_importer.get_or_create_image(src.normal_texture))
        g.connect('NormalTexture', normal_texture, 'Color')

    if src.matcap_texture:
        #
        # https://dskjal.com/blender/ibl-to-uv.html
        #
        texture_coords = factory.create('TexCoord', -1200, -1200)

        # to camera coords
        vector_transform = factory.create('VectorTransform', -1000, -1200)
        vector_transform.node.convert_from = 'OBJECT'
        vector_transform.node.convert_to = 'CAMERA'
        vector_transform.connect('Vector', texture_coords, 'Normal')

        mapping = factory.create('Mapping', -800, -1200)
        mapping.node.vector_type = 'POINT'
        mapping.set_default_value('Location', (0.5, 0.5, 0))
        mapping.set_default_value('Rotation', (radians(90), 0, 0))
        mapping.connect('Vector', vector_transform)

        matcap_texture = factory.create('TexImage', -600, -1200)
        matcap_texture.node.label = 'Matcap'
        matcap_texture.set_image(
            texture_importer.get_or_create_image(src.matcap_texture))
        matcap_texture.connect('Vector', mapping)

        g.connect('MatcapTexture', matcap_texture, 'Color')
