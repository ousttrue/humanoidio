from logging import getLogger
logger = getLogger(__name__)
import bpy
from .. import pyscene
from .wrap_node import WrapNodeFactory, WrapNode
from .texture_importer import TextureImporter
from .prefix import PREFIX


class GltfPBR:
    GROUP_NAME = f'{PREFIX}:PBR'

    @classmethod
    def get_or_create(cls) -> bpy.types.NodeTree:
        g = bpy.data.node_groups.get(cls.GROUP_NAME)
        if g:
            return g

        logger.debug(f'node group: {cls.GROUP_NAME}')
        g = bpy.data.node_groups.new(cls.GROUP_NAME, type='ShaderNodeTree')
        factory = WrapNodeFactory(g)

        #
        # input
        #
        group_inputs = g.nodes.new('NodeGroupInput')
        group_inputs.select = False
        group_inputs.location = (-1000, 0)

        # base color
        g.inputs.new('NodeSocketColor',
                     'BaseColor').default_value = (1, 1, 1, 1)
        g.inputs.new('NodeSocketColor', 'BaseColorTexture')
        g.inputs.new('NodeSocketFloat', 'Alpha').default_value = 1

        # metallic
        g.inputs.new('NodeSocketColor', 'MetallicRoughnessTexture')
        g.inputs.new('NodeSocketFloat', 'Metallic').default_value = 1
        g.inputs.new('NodeSocketFloat', 'Roughness').default_value = 1

        # occlusion
        g.inputs.new('NodeSocketColor',
                     'OcclusionTexture').default_value = (0, 0, 0, 1)
        g.inputs.new('NodeSocketFloat', 'OcclusionStrength').default_value = 1

        # emission
        g.inputs.new('NodeSocketColor',
                     'Emission').default_value = (0, 0, 0, 1)
        g.inputs.new('NodeSocketColor',
                     'EmissiveTexture').default_value = (0, 0, 0, 0)

        # normal
        g.inputs.new('NodeSocketFloat', 'NormalScale').default_value = 1
        g.inputs.new('NodeSocketColor', 'NormalTexture')

        input = WrapNode(g.links, group_inputs)

        color = factory.create('MixRGB', -400, 300)
        color.node.blend_type = 'MULTIPLY'  # type: ignore
        color.set_default_value('Fac', 1)
        color.connect('Color1', input, 'BaseColor')
        color.connect('Color2', input, 'BaseColorTexture')

        separate = factory.create('SeparateRGB', -700)
        separate.connect('Image', input, 'MetallicRoughnessTexture')

        metallic = factory.create('Math', -400, 100)
        metallic.node.operation = 'MULTIPLY'  # type: ignore
        metallic.connect(0, input, 'Metallic')
        metallic.connect(1, separate, 'B')

        roughness = factory.create('Math', -400, -100)
        roughness.node.operation = 'MULTIPLY'  # type: ignore
        roughness.connect(0, input, 'Roughness')
        roughness.connect(1, separate, 'G')

        emission = factory.create('MixRGB', -400, -300)
        emission.node.blend_type = 'MULTIPLY'  # type: ignore
        emission.set_default_value('Fac', 1)
        emission.connect('Color1', input, 'Emission')
        emission.connect('Color2', input, 'EmissiveTexture')

        normal_map = factory.create('NormalMap', -400, -500)
        normal_map.connect('Strength', input, 'NormalScale')
        normal_map.connect('Color', input, 'NormalTexture')

        #
        # bsdf
        #
        bsdf = factory.create('BsdfPrincipled')
        bsdf.connect('Base Color', color)
        bsdf.connect('Metallic', metallic)
        bsdf.connect('Roughness', roughness)
        bsdf.connect('Emission', emission)
        bsdf.connect('Normal', normal_map)

        #
        # outut
        #
        group_outputs = g.nodes.new('NodeGroupOutput')
        group_outputs.select = False
        group_outputs.location = (300, 0)
        g.outputs.new('NodeSocketShader', 'Shader')
        output = WrapNode(g.links, group_outputs)
        output.connect('Shader', bsdf)

        return g


def build(bl_material: bpy.types.Material, src: pyscene.PBRMaterial,
          texture_importer: TextureImporter):
    '''
    BsdfPrincipled
    '''
    factory = WrapNodeFactory(bl_material.node_tree)

    pbr = factory.create('Group', -400)
    pbr.node.node_tree = GltfPBR.get_or_create()  # type: ignore
    pbr.set_default_value('BaseColor',
                          (src.color.x, src.color.y, src.color.z, 1))
    pbr.set_default_value('Alpha', src.color.w)
    pbr.set_default_value(
        'Emission',
        (src.emissive_color.x, src.emissive_color.y, src.emissive_color.z, 1))
    pbr.set_default_value('Metallic', src.metallic)
    pbr.set_default_value('Roughness', src.roughness)
    pbr.set_default_value('NormalScale', src.normal_scale)
    # pbr.set_default_value('OcclusionStrength', src.occlusion)

    # build node
    output = factory.create('OutputMaterial')
    output.connect('Surface', pbr)

    # color texture
    if src.color_texture:
        color_texture = factory.create('TexImage', -800)
        color_texture.node.label = 'BaseColorTexture'
        color_texture.set_image(
            texture_importer.get_or_create_image(src.color_texture))
        pbr.connect('BaseColorTexture', color_texture)
        pbr.connect('Alpha', color_texture, 'Alpha')

    # metallic roughness
    if src.metallic_roughness_texture:

        metallic_roughness_texture = factory.create('TexImage', -800, -300)
        metallic_roughness_texture.node.label = 'MetallicRoughnessTexture'
        metallic_roughness_texture.set_image(
            texture_importer.get_or_create_image(
                src.metallic_roughness_texture))
        pbr.connect('MetallicRoughnessTexture', metallic_roughness_texture)

    # occlusion
    if src.occlusion_texture:
        occlusion_texture = factory.create('TexImage', -800, -600)
        occlusion_texture.node.label = 'OcclusionTexture'
        occlusion_texture.set_image(
            texture_importer.get_or_create_image(src.occlusion_texture))
        pbr.connect('OcclusionTexture', occlusion_texture)

    # emission
    if src.emissive_texture:
        emissive_texture = factory.create('TexImage', -800, -900)
        emissive_texture.node.label = 'EmissiveTexture'
        emissive_texture.set_image(
            texture_importer.get_or_create_image(src.emissive_texture))
        pbr.connect('EmissiveTexture', emissive_texture)

    # normal map
    if src.normal_texture:
        normal_texture = factory.create('TexImage', -800, -1200)
        normal_texture.node.label = 'NormalTexture'
        normal_texture.set_image(
            texture_importer.get_or_create_image(src.normal_texture))
        pbr.connect('NormalTexture', normal_texture)
