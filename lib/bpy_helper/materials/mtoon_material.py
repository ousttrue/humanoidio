from logging import getLogger
from math import radians
logger = getLogger(__name__)
import bpy, mathutils
from .. import pyscene
from .texture_importer import TextureImporter
from .wrap_node import WrapNode, WrapNodeFactory


class MatcapUV:
    GROUP_NAME = 'pyimpex:MatcapUV'

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
        vector_transform.node.vector_type = 'NORMAL'
        vector_transform.node.convert_from = 'OBJECT'
        vector_transform.node.convert_to = 'CAMERA'
        vector_transform.connect('Vector', texture_coords, 'Normal')

        mapping_scale = factory.create('Mapping', -600)
        mapping_scale.node.vector_type = 'POINT'
        mapping_scale.set_default_value('Scale', (0.5, 0.5, 0.5))
        mapping_scale.connect('Vector', vector_transform)

        mapping_location = factory.create('Mapping', -300)
        mapping_location.node.vector_type = 'POINT'
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


class MToonGroup:
    GROUP_NAME = 'pyimpex:MToon'

    @classmethod
    def get_or_create(cls) -> bpy.types.NodeTree:
        '''
        normal -> bsdf -> to_rgb -> ramp -> mix -> mult -> out
                                            shade   color
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
        # emission
        g.inputs.new('NodeSocketColor',
                     'Emission').default_value = (0, 0, 0, 1)
        g.inputs.new('NodeSocketColor',
                     'EmissiveTexture').default_value = (1, 1, 1, 1)

        g.inputs.new('NodeSocketFloat', 'Alpha').default_value = 1
        g.inputs.new('NodeSocketColor',
                     'MatcapTexture').default_value = (0, 0, 0, 0)

        # color shade
        g.inputs.new('NodeSocketColor', 'Color').default_value = (1, 1, 1, 1)
        g.inputs.new('NodeSocketColor',
                     'ColorTexture').default_value = (1, 1, 1, 1)
        # shade toon
        g.inputs.new('NodeSocketColor',
                     'ShadeColor').default_value = (1, 1, 1, 1)
        g.inputs.new('NodeSocketColor',
                     'ShadeColorTexture').default_value = (1, 1, 1, 1)
        g.inputs.new('NodeSocketFloat', 'ShadeToony').default_value = 0.9
        g.inputs.new('NodeSocketFloat', 'ShadingShift').default_value = 0

        # normal
        g.inputs.new('NodeSocketColor',
                     'NormalTexture').default_value = (0.5, 0.5, 1, 1)
        g.inputs.new('NodeSocketFloat', 'NormalStrength').default_value = 1
        # gamma(VRM-0.X)
        g.inputs.new('NodeSocketFloat', 'ColorGamma').default_value = 2.2
        input = WrapNode(g.links, group_inputs)

        #
        # shading
        #
        normal_map = factory.create('NormalMap', -600, -500)
        normal_map.connect('Color', input, 'NormalTexture')
        normal_map.connect('Strength', input, 'NormalStrength')

        bsdf = factory.create('BsdfDiffuse', -300, -700)
        bsdf.set_default_value('Roughness', 1)
        bsdf.connect('Normal', normal_map)

        # emission x emission_texture
        mult_emission = factory.create('MixRGB', -600, 300)
        mult_emission.node.blend_type = 'MULTIPLY'  # type: ignore
        mult_emission.set_default_value('Fac', 1)
        mult_emission.connect('Color1', input, 'Emission')
        mult_emission.connect('Color2', input, 'EmissiveTexture')

        emission = factory.create('Emission', -300, 300)
        emission.connect('Color', mult_emission)

        #
        # matcap
        #
        matcap = factory.create('Emission', -600, 50)
        matcap.connect('Color', input, 'MatcapTexture')

        # color x color_texture
        color_gamma = factory.create('Gamma', -800, -100)
        color_gamma.connect('Gamma', input, 'ColorGamma')
        color_gamma.connect('Color', input, 'Color')
        mult_color = factory.create('MixRGB', -600, -100)
        mult_color.node.blend_type = 'MULTIPLY'  # type: ignore
        mult_color.set_default_value('Fac', 1)
        mult_color.connect('Color1', color_gamma)
        mult_color.connect('Color2', input, 'ColorTexture')

        shade_gamma = factory.create('Gamma', -800, -200)
        shade_gamma.connect('Gamma', input, 'ColorGamma')
        shade_gamma.connect('Color', input, 'ShadeColor')
        mult_shade = factory.create('MixRGB', -600, -300)
        mult_shade.node.blend_type = 'MULTIPLY'  # type: ignore
        mult_shade.set_default_value('Fac', 1)
        mult_shade.connect('Color1', shade_gamma)
        mult_shade.connect('Color2', input, 'ShadeColorTexture')

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
        ramp_mix.connect('Color1', mult_shade)
        ramp_mix.set_default_value('Color2', (1, 1, 1, 1))

        # color x shade
        mult_shade = factory.create('MixRGB', 0, -200)
        mult_shade.node.blend_type = 'MULTIPLY'  # type: ignore
        mult_shade.set_default_value('Fac', 1)
        mult_shade.connect('Color1', mult_color)
        mult_shade.connect('Color2', ramp_mix)

        shade_emission = factory.create('Emission', 100, -100)
        shade_emission.connect('Color', mult_shade)

        add_shader = factory.create('AddShader', 100)
        add_shader.connect(0, matcap)
        add_shader.connect(1, shade_emission)

        add_emission = factory.create('AddShader', 0, 100)
        add_emission.connect(0, emission)
        add_emission.connect(1, add_shader)

        transparent = factory.create('BsdfTransparent', -400, 100)

        mix = factory.create('MixShader', -200, 200)
        mix.connect('Fac', input, 'Alpha')
        mix.connect(1, transparent)
        mix.connect(2, add_emission)

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
    factory = WrapNodeFactory(bl_material.node_tree)

    g = factory.create('Group', -300)
    g.node.node_tree = MToonGroup.get_or_create()
    g.set_default_value('Color', (src.color.x, src.color.y, src.color.z, 1))
    g.set_default_value(
        'ShadeColor',
        (src.shade_color.x, src.shade_color.y, src.shade_color.z, 1))
    g.set_default_value('ShadeToony', src.shade_toony)
    g.set_default_value('ShadingShift', src.shading_shift)
    g.set_default_value(
        'Emission',
        (src.emissive_color.x, src.emissive_color.y, src.emissive_color.z, 1))
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
        matcap = factory.create('Group', -800, -1200)
        matcap.node.node_tree = MatcapUV.get_or_create()

        matcap_texture = factory.create('TexImage', -600, -1200)
        matcap_texture.node.label = 'Matcap'
        matcap_texture.set_image(
            texture_importer.get_or_create_image(src.matcap_texture))
        matcap_texture.connect('Vector', matcap)

        g.connect('MatcapTexture', matcap_texture, 'Color')
