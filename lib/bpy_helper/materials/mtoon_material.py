'''
https://github.com/Santarh/MToon/blob/master/MToon/Resources/Shaders/MToonCore.cginc
'''

from logging import getLogger
logger = getLogger(__name__)
from math import radians
import bpy, mathutils
from .. import pyscene
from .texture_importer import TextureImporter
from .wrap_node import WrapNode, WrapNodeFactory
from .prefix import PREFIX


class MatcapUV:
    GROUP_NAME = f'{PREFIX}:MatcapUV'

    @classmethod
    def get_or_create(cls):
        g = bpy.data.node_groups.get(cls.GROUP_NAME)
        if g:
            return g

        logger.debug(f'node group: {cls.GROUP_NAME}')
        g = bpy.data.node_groups.new(cls.GROUP_NAME, type='ShaderNodeTree')
        factory = WrapNodeFactory(g)

        texture_coords = factory.create('TexCoord', -1500)

        # to camera coords
        vector_transform = factory.create('VectorTransform', -1200)
        vector_transform.node.vector_type = 'NORMAL'  # type: ignore
        vector_transform.node.convert_from = 'OBJECT'  # type: ignore
        vector_transform.node.convert_to = 'CAMERA'  # type: ignore
        vector_transform.connect('Vector', texture_coords, 'Normal')

        mapping_scale = factory.create('Mapping', -600)
        mapping_scale.node.vector_type = 'POINT'  # type: ignore
        mapping_scale.set_default_value('Scale', (0.5, 0.5, 0.5))
        mapping_scale.connect('Vector', vector_transform)

        mapping_location = factory.create('Mapping', -300)
        mapping_location.node.vector_type = 'POINT'  # type: ignore
        mapping_location.set_default_value('Location', (0.5, 0.5, 0))
        mapping_location.connect('Vector', mapping_scale)

        # create group outputs
        group_outputs = g.nodes.new('NodeGroupOutput')
        group_outputs.select = False
        group_outputs.location = (0, 200)
        g.outputs.new('NodeSocketVector', 'Vector')
        output = WrapNode(g.links, group_outputs)
        output.connect('Vector', mapping_location)

        return g


class ToonShading:
    '''
    Lighting を解決する(toon shading)

    const float EPS_COL = 0.00001;
    half maxIntensityThreshold = lerp(1, _ShadeShift, _ShadeToony);
    half minIntensityThreshold = _ShadeShift;
    lightIntensity = saturate((lightIntensity - minIntensityThreshold) / max(EPS_COL, (maxIntensityThreshold - minIntensityThreshold)));

    '''
    GROUP_NAME = f'{PREFIX}:Toon'

    @classmethod
    def get_or_create(cls) -> bpy.types.NodeTree:

        g = bpy.data.node_groups.get(cls.GROUP_NAME)
        if g:
            return g

        logger.debug(f'node group: {cls.GROUP_NAME}')
        g = bpy.data.node_groups.new(cls.GROUP_NAME, type='ShaderNodeTree')
        factory = WrapNodeFactory(g)

        #
        # inputs
        #
        group_inputs = g.nodes.new('NodeGroupInput')
        group_inputs.select = False
        group_inputs.location = (-600, 0)

        # normal
        g.inputs.new('NodeSocketFloat', 'NormalStrength').default_value = 1
        g.inputs.new('NodeSocketColor',
                     'NormalTexture').default_value = (0.5, 0.5, 1, 1)

        # shade color
        g.inputs.new('NodeSocketFloat', 'ShadingShift').default_value = 0
        g.inputs.new('NodeSocketFloat', 'ShadeToony').default_value = 0.9

        input = WrapNode(g.links, group_inputs)

        #
        # numerator
        #
        normal_map = factory.create('NormalMap', -300, 100)
        normal_map.connect('Color', input, 'NormalTexture')
        normal_map.connect('Strength', input, 'NormalStrength')

        bsdf = factory.create('BsdfDiffuse', 0, 100)
        bsdf.set_default_value('Roughness', 1)
        bsdf.connect('Normal', normal_map)

        to_rgb = factory.create('ShaderToRGB', 300, 100)
        to_rgb.connect('Shader', bsdf)

        intensity_shift = factory.create('Math', 600, 100)
        intensity_shift.node.operation = 'SUBTRACT'  # type: ignore
        intensity_shift.connect(0, to_rgb)
        intensity_shift.connect(1, input, 'ShadingShift')

        #
        # denominator
        #
        map_range = factory.create('MapRange', -300, -200)
        map_range.connect('Value', input, 'ShadeToony')
        map_range.set_default_value('To Min', 1)
        map_range.connect('To Max', input, 'ShadingShift')

        toony_shift = factory.create('Math', 0, -200)
        toony_shift.node.operation = 'SUBTRACT'  # type: ignore
        toony_shift.connect(0, map_range)
        toony_shift.connect(1, input, 'ShadingShift')

        max = factory.create('Math', 300, -200)
        max.node.operation = 'MAXIMUM'  # type: ignore
        max.connect(0, toony_shift)
        max.set_default_value(1, 0.00001)  # EPSILON

        #
        # divide
        #
        divide = factory.create('Math', 900)
        divide.node.operation = 'DIVIDE'  # type: ignore
        divide.connect(0, intensity_shift)
        divide.connect(1, max)

        clamp = factory.create('Clamp', 900, 300)
        clamp.connect(0, divide)

        # create group outputs
        group_outputs = g.nodes.new('NodeGroupOutput')
        group_outputs.select = False
        group_outputs.location = (900, 600)
        g.outputs.new('NodeSocketColor', 'Diffuse')
        g.outputs.new('NodeSocketFloat', 'Toon')
        output = WrapNode(g.links, group_outputs)
        output.connect('Diffuse', to_rgb)
        output.connect('Toon', clamp)

        return g


class MToonGroup:
    GROUP_NAME = f'{PREFIX}:MToon'

    @classmethod
    def get_or_create(cls) -> bpy.types.NodeTree:
        '''
        alpha
        emission
        matcap
        intensity x color
        '''

        g = bpy.data.node_groups.get(cls.GROUP_NAME)
        if g:
            return g

        logger.debug(f'node group: {cls.GROUP_NAME}')
        g = bpy.data.node_groups.new(cls.GROUP_NAME, type='ShaderNodeTree')
        factory = WrapNodeFactory(g)

        #
        # inputs
        #
        group_inputs = g.nodes.new('NodeGroupInput')
        group_inputs.select = False
        group_inputs.location = (-1000, 0)
        # toon
        g.inputs.new('NodeSocketColor', 'Diffuse')
        g.inputs.new('NodeSocketFloat', 'Alpha').default_value = 1
        # emission
        g.inputs.new('NodeSocketColor',
                     'Emission').default_value = (0, 0, 0, 1)
        g.inputs.new('NodeSocketColor',
                     'EmissiveTexture').default_value = (1, 1, 1, 1)

        g.inputs.new('NodeSocketColor',
                     'MatcapTexture').default_value = (0, 0, 0, 0)

        g.inputs.new('NodeSocketFloat', 'Toon')
        # gamma(VRM-0.X)
        g.inputs.new('NodeSocketFloat', 'ColorGamma').default_value = 2.2
        # shade color
        g.inputs.new('NodeSocketColor',
                     'ShadeColor').default_value = (1, 1, 1, 1)
        g.inputs.new('NodeSocketColor',
                     'ShadeColorTexture').default_value = (1, 1, 1, 1)
        # color shade
        g.inputs.new('NodeSocketColor', 'Color').default_value = (1, 1, 1, 1)
        g.inputs.new('NodeSocketColor',
                     'ColorTexture').default_value = (1, 1, 1, 1)

        input = WrapNode(g.links, group_inputs)

        # emission x emission_texture
        mult_emission = factory.create('MixRGB', -600, 300)
        mult_emission.node.blend_type = 'MULTIPLY'  # type: ignore
        mult_emission.set_default_value('Fac', 1)
        mult_emission.connect('Color1', input, 'Emission')
        mult_emission.connect('Color2', input, 'EmissiveTexture')

        emission = factory.create('Emission', -200, 300)
        emission.connect('Color', mult_emission)

        #
        # matcap
        #
        matcap = factory.create('Emission', -200, 100)
        matcap.connect('Color', input, 'MatcapTexture')

        #
        # color
        #

        # shade x shade_texture
        shade_gamma = factory.create('Gamma', -800, -100)
        shade_gamma.connect('Gamma', input, 'ColorGamma')
        shade_gamma.connect('Color', input, 'ShadeColor')
        mult_shade = factory.create('MixRGB', -600, -100)
        mult_shade.node.blend_type = 'MULTIPLY'  # type: ignore
        mult_shade.set_default_value('Fac', 1)
        mult_shade.connect('Color1', shade_gamma)
        mult_shade.connect('Color2', input, 'ShadeColorTexture')

        # color x color_texture
        color_gamma = factory.create('Gamma', -800, -300)
        color_gamma.connect('Gamma', input, 'ColorGamma')
        color_gamma.connect('Color', input, 'Color')
        mult_color = factory.create('MixRGB', -600, -300)
        mult_color.node.blend_type = 'MULTIPLY'  # type: ignore
        mult_color.set_default_value('Fac', 1)
        mult_color.connect('Color1', color_gamma)
        mult_color.connect('Color2', input, 'ColorTexture')

        # color x shade
        mix = factory.create('MixRGB', -400, -100)
        mix.node.blend_type = 'MIX'  # type: ignore
        mix.connect('Fac', input, 'Toon')
        mix.connect('Color1', mult_shade)
        mix.connect('Color2', mult_color)

        shade_emission = factory.create('Emission', -200, -100)
        shade_emission.connect('Color', mix)

        #
        # add
        #
        add_shader = factory.create('AddShader', 100, 100)
        add_shader.connect(0, matcap)
        add_shader.connect(1, shade_emission)

        add_emission = factory.create('AddShader', 100, 300)
        add_emission.connect(0, emission)
        add_emission.connect(1, add_shader)

        transparent = factory.create('BsdfTransparent', -200, 500)
        mix = factory.create('MixShader', 100, 500)
        mix.connect('Fac', input, 'Alpha')
        mix.connect(1, transparent)
        mix.connect(2, add_emission)

        # create group outputs
        group_outputs = g.nodes.new('NodeGroupOutput')
        group_outputs.select = False
        group_outputs.location = (400, 500)
        g.outputs.new('NodeSocketShader', 'Surface')
        output = WrapNode(g.links, group_outputs)
        output.connect('Surface', mix)

        return g


def build(bl_material: bpy.types.Material, src: pyscene.MToonMaterial,
          texture_importer: TextureImporter):
    factory = WrapNodeFactory(bl_material.node_tree)

    #
    # toon
    #
    shading = factory.create('Group', -300, 300)
    shading.node.node_tree = ToonShading.get_or_create()  # type: ignore
    shading.set_default_value('ShadeToony', src.shade_toony)
    shading.set_default_value('ShadingShift', src.shading_shift)
    if src.normal_texture:
        normal_texture = factory.create('TexImage', -600, 300)
        normal_texture.node.label = 'NormalTexture'
        normal_texture.set_image(
            texture_importer.get_or_create_image(src.normal_texture))
        shading.connect('NormalTexture', normal_texture, 'Color')

    #
    # mtoon
    #
    mtoon = factory.create('Group')
    mtoon.node.node_tree = MToonGroup.get_or_create()  # type: ignore
    mtoon.set_default_value('Color',
                            (src.color.x, src.color.y, src.color.z, 1))
    mtoon.set_default_value(
        'ShadeColor',
        (src.shade_color.x, src.shade_color.y, src.shade_color.z, 1))
    mtoon.set_default_value(
        'Emission',
        (src.emissive_color.x, src.emissive_color.y, src.emissive_color.z, 1))
    mtoon.connect('Diffuse', shading, 'Diffuse')
    mtoon.connect('Toon', shading, 'Toon')

    #
    # out
    #
    out = factory.create('OutputMaterial', 300)
    out.connect('Surface', mtoon)

    if src.emissive_texture:
        emissive_texture = factory.create('TexImage', -600)
        emissive_texture.node.label = 'EmissiveTexture'
        emissive_texture.set_image(
            texture_importer.get_or_create_image(src.emissive_texture))
        mtoon.connect('EmissiveTexture', emissive_texture, 'Color')

    if src.matcap_texture:
        matcap = factory.create('Group', -900, -300)
        matcap.node.node_tree = MatcapUV.get_or_create()  # type: ignore

        matcap_texture = factory.create('TexImage', -600, -300)
        matcap_texture.node.label = 'Matcap'
        matcap_texture.set_image(
            texture_importer.get_or_create_image(src.matcap_texture))
        matcap_texture.connect('Vector', matcap)

        mtoon.connect('MatcapTexture', matcap_texture, 'Color')

    if src.color_texture:
        color_texture = factory.create('TexImage', -600, -600)
        color_texture.node.label = 'BaseColorTexture'
        color_texture.set_image(
            texture_importer.get_or_create_image(src.color_texture))
        mtoon.connect('ColorTexture', color_texture, 'Color')
        mtoon.connect('Alpha', color_texture, 'Alpha')

    if src.shade_texture:
        shade_texture = factory.create('TexImage', -600, -900)
        shade_texture.node.label = 'ShadeColorTexture'
        shade_texture.set_image(
            texture_importer.get_or_create_image(src.shade_texture))
        mtoon.connect('ShadeColorTexture', shade_texture, 'Color')
