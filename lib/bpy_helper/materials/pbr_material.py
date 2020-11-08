from logging import getLogger
logger = getLogger(__name__)
from typing import List, Optional
import bpy
from ... import pyscene
from ...struct_types import Float4
from .wrap_node import WrapNodeFactory, WrapNode
from .texture_importer import TextureImporter
from .prefix import PREFIX
from .group_input import GroupInput, nodegroup_from_inputs
from .texture_exporter import export_texture


class GltfPBR:
    GROUP_NAME = f'{PREFIX}:PBR'

    GROUP_INPUTS: List[GroupInput] = [
        GroupInput('BaseColor', 'Color', (1, 1, 1, 1)),
        GroupInput('BaseColorTexture', 'Color'),
        GroupInput('Alpha', 'Float', 1),
        GroupInput('MetallicRoughnessTexture', 'Color'),
        GroupInput('Metallic', 'Float', 1),
        GroupInput('Roughness', 'Float', 1),
        GroupInput('OcclusionTexture', 'Color', (0, 0, 0, 1)),
        GroupInput('OcclusionStrength', 'Float', 1),
        GroupInput('Emission', 'Color', (0, 0, 0, 1)),
        GroupInput('EmissiveTexture', 'Color', (0, 0, 0, 0)),
        GroupInput('NormalScale', 'Float', 1),
        GroupInput('NormalTexture', 'Color'),
    ]

    @classmethod
    def get_or_create(cls) -> bpy.types.NodeTree:
        g = bpy.data.node_groups.get(cls.GROUP_NAME)
        if g:
            return g

        logger.debug(f'node group: {cls.GROUP_NAME}')
        g = nodegroup_from_inputs(cls.GROUP_NAME, cls.GROUP_INPUTS)
        factory = WrapNodeFactory(g)

        #
        # input
        #
        group_inputs = g.nodes.new('NodeGroupInput')
        group_inputs.select = False
        group_inputs.location = (-1000, 0)
        input = WrapNode(g.links, group_inputs)

        # links
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


def export(m: bpy.types.Material,
           g: bpy.types.ShaderNodeGroup) -> pyscene.PBRMaterial:
    material = pyscene.PBRMaterial(m.name)

    for k, socket in g.inputs.items():  # type: ignore
        v = socket.default_value
        if k == 'BaseColor':
            material.color.x = v[0]
            material.color.y = v[1]
            material.color.z = v[2]
        elif k == 'BaseColorTexture':
            material.color_texture = export_texture(m.node_tree, socket)
        elif k == 'Alpha':
            material.color.w = v
        elif k == 'Metallic':
            material.metallic = v
        elif k == 'Roughness':
            material.roughness = v
        elif k == 'MetallicRoughnessTexture':
            pass
        elif k == 'OcclusionStrength':
            material.occlusion_strength = v
        elif k == 'OcclusionTexture':
            pass
        elif k == 'Emission':
            material.emissive_color.x = v[0]
            material.emissive_color.y = v[1]
            material.emissive_color.z = v[2]
        elif k == 'EmissiveTexture':
            pass
        elif k == 'NormalScale':
            material.normal_scale = v
        elif k == 'NormalTexture':
            pass
        else:
            print(k, v)

    return material
