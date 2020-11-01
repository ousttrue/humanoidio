from typing import Callable
import bpy
from .wrap_node import WrapNode
from .. import pyscene


def build_unlit(bl_material: bpy.types.Material, src: pyscene.UnlitMaterial,
                get_or_create_image: Callable[[pyscene.Texture],
                                              bpy.types.Image]):
    '''
    out -> mix Fac-> alpha ------------>|
               Sahder1 -> transparent   | TexImage
               Shader2 -> color ------->|
    '''
    bl_material.use_nodes = True
    bl_material.node_tree.nodes.clear()

    def create(name: str, x=0, y=0) -> WrapNode:
        if not name.startswith("ShaderNode"):
            name = "ShaderNode" + name
        node = bl_material.node_tree.nodes.new(type=name)
        node.location = (x, y)
        # return node
        return WrapNode(bl_material.node_tree.links, node)

    out = create('OutputMaterial')
    mix = create('MixShader', -200, 0)
    mix.set_default_value('Fac', src.color[3])
    out.link('Surface', mix)

    transparent = create('BsdfTransparent', -400, 0)
    mix.link(1, transparent)

    color = create('MixRGB', -400, -200)
    color.node.blend_type = 'MULTIPLY'
    color.set_default_value('Color1',
                            (src.color[0], src.color[1], src.color[2], 1))
    color.set_default_value('Color2', (1, 1, 1, 1))
    color.set_default_value('Fac', 1)
    mix.link(2, color)

    if src.color_texture:
        color_texture = create('TexImage', -600, -100)
        color_texture.node.image = get_or_create_image(
            src.color_texture)  # type: ignore
        color.link('Color2', color_texture)
        mix.link('Fac', color_texture, 'Alpha')

    for n in bl_material.node_tree.nodes:
        n.select = False
