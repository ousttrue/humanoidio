import bpy
from .. import pyscene
from .texture_importer import TextureImporter
from . import wrap_node


def build_pbr(bl_material: bpy.types.Material, src: pyscene.PBRMaterial,
              texture_importer: TextureImporter):
    '''
    BsdfPrincipled
    '''
    factory = wrap_node.WrapNodeFactory(bl_material)

    # build node
    output = factory.create('OutputMaterial')
    bsdf = factory.create('BsdfPrincipled', -300)
    # bsdf_node.set_default_value(
    #     'Base Color', (src.color.x, src.color.y, src.color.z, src.color.w))
    output.connect('Surface', bsdf)

    color = factory.create('MixRGB', -500)
    color.node.blend_type = 'MULTIPLY'  # type: ignore
    color.set_default_value('Fac', 1)
    color.set_default_value('Color1',
                            (src.color[0], src.color[1], src.color[2], 1))
    bsdf.connect('Base Color', color)

    if src.color_texture:
        # color texture
        color_texture = factory.create('TexImage', -800)
        color_texture.node.label = 'BaseColorTexture'
        color_texture.set_image(
            texture_importer.get_or_create_image(src.color_texture))
        color.connect('Color2', color_texture, 'Color')
        bsdf.connect('Alpha', color_texture, 'Alpha')

    # metallic roughness
    if src.metallic_roughness_texture:
        separate = factory.create('SeparateRGB', -500, -300)
        bsdf.connect('Roughness', separate, 'G')
        bsdf.connect('Metallic', separate, 'B')

        metallic_roughness_texture = factory.create('TexImage', -800, -300)
        metallic_roughness_texture.node.label = 'MetallicRoughnessTexture'
        metallic_roughness_texture.set_image(
            texture_importer.get_or_create_image(
                src.metallic_roughness_texture))
        separate.connect('Image', metallic_roughness_texture)

    # emissive
    emissive = factory.create('MixRGB', -500, -600)
    emissive.node.blend_type = 'MULTIPLY'  # type: ignore
    emissive.set_default_value('Fac', 1)
    emissive.set_default_value('Color1',
                               (src.emissive_color[0], src.emissive_color[1],
                                src.emissive_color[2], 1))
    bsdf.connect('Emission', emissive)
    if src.emissive_texture:
        emissive_texture = factory.create('TexImage', -800, -600)
        emissive_texture.node.label = 'EmissiveTexture'
        emissive_texture.set_image(
            texture_importer.get_or_create_image(src.emissive_texture))
        emissive.connect('Color2', emissive_texture, 'Color')

    # normal map
    if src.normal_texture:
        normal_map = factory.create('NormalMap', -500, -900)
        normal_map.set_default_value('Strength', src.normal_scale)
        bsdf.connect('Normal', normal_map)

        normal_texture = factory.create('TexImage', -800, -900)
        normal_texture.node.label = 'NormalTexture'
        normal_texture.set_image(
            texture_importer.get_or_create_image(src.normal_texture))
        normal_map.connect('Color', normal_texture, 'Color')

    # ToDo:
    # if src.occlusion_texture:
    #     pass
