import bpy
from .. import pyscene
from . import wrap_node
from .texture_importer import TextureImporter


def build_unlit(bl_material: bpy.types.Material, src: pyscene.UnlitMaterial,
                texture_importer: TextureImporter):
    '''
    out -> mix Fac-> alpha ------------>|
               Sahder1 -> transparent   | TexImage
               Shader2 -> color ------->|
    '''
    factory = wrap_node.WrapNodeFactory(bl_material)

    out = factory.create('OutputMaterial')
    mix = factory.create('MixShader', -200, 0)
    mix.set_default_value('Fac', src.color[3])
    out.connect('Surface', mix)

    transparent = factory.create('BsdfTransparent', -400, 0)
    mix.connect(1, transparent)

    color = factory.create('MixRGB', -400, -200)
    color.node.blend_type = 'MULTIPLY'
    color.set_default_value('Fac', 1)
    color.set_default_value('Color1',
                            (src.color[0], src.color[1], src.color[2], 1))
    color.set_default_value('Color2', (1, 1, 1, 1))
    mix.connect(2, color)

    if src.color_texture:
        color_texture = factory.create('TexImage', -600, -100)
        color_texture.node.image = texture_importer.get_or_create_image(
            src.color_texture)  # type: ignore
        color.connect('Color2', color_texture)
        mix.connect('Fac', color_texture, 'Alpha')
