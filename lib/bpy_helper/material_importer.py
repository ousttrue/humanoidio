from typing import Dict, List
import PIL.Image
import PIL.ImageOps
import bpy, mathutils
from .. import pyscene


class NodePostion:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def increment(self, node: bpy.types.ShaderNode):
        node.location = (self.x, self.y)
        self.x -= 100


class MaterialImporter:
    def __init__(self):
        self.material_map: Dict[pyscene.Material, bpy.types.Material] = {}
        self.image_map: Dict[pyscene.Texture, bpy.types.Image] = {}

    def get_or_create_material(
            self, material: pyscene.Material) -> bpy.types.Material:
        bl_material = self.material_map.get(material)
        if bl_material:
            return bl_material

        # base color
        bl_material: bpy.types.Material = bpy.data.materials.new(material.name)
        bl_material.diffuse_color = (material.color.x, material.color.y,
                                     material.color.z, material.color.w)
        self.material_map[material] = bl_material
        bl_material.use_backface_culling = not material.double_sided

        # alpha blend
        if material.blend_mode == pyscene.BlendMode.Opaque:
            bl_material.blend_method = 'OPAQUE'
        elif material.blend_mode == pyscene.BlendMode.AlphaBlend:
            bl_material.blend_method = 'BLEND'
        elif material.blend_mode == pyscene.BlendMode.Mask:
            bl_material.blend_method = 'CLIP'
            bl_material.alpha_threshold = material.threshold

        if isinstance(material, pyscene.PBRMaterial):
            # PBR
            self.create_pbr(bl_material, material)
        else:
            # unlit
            self.create_unlit(bl_material, material)

        return bl_material

    def _get_or_create_image(self,
                             texture: pyscene.Texture) -> bpy.types.Image:
        bl_image = self.image_map.get(texture)
        if bl_image:
            return bl_image

        image = texture.image

        if image.mode == 'RGBA':
            image = PIL.ImageOps.flip(image)
            bl_image = bpy.data.images.new(texture.name,
                                           alpha=True,
                                           width=image.width,
                                           height=image.height)
            # RGBA[0-255] to float[0-1]
            pixels = [e / 255 for pixel in image.getdata() for e in pixel]
            bl_image.pixels = pixels

        elif image.mode == 'RGB':
            image = PIL.ImageOps.flip(image)
            image = image.convert('RGBA')
            bl_image = bpy.data.images.new(texture.name,
                                           alpha=False,
                                           width=image.width,
                                           height=image.height)

            # RGBA[0-255] to float[0-1]
            pixels = [e / 255 for pixel in image.getdata() for e in pixel]
            bl_image.pixels = pixels

        else:
            raise NotImplementedError()

        self.image_map[texture] = bl_image
        return bl_image

    def create_unlit(self, bl_material: bpy.types.Material,
                     src: pyscene.Material):
        bl_material.use_nodes = True
        nodes: bpy.types.Nodes = bl_material.node_tree.nodes
        links: bpy.types.NodeLinks = bl_material.node_tree.links

        # clear nodes
        nodes.clear()

        # build node
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        mix_node = nodes.new(type="ShaderNodeMixRGB")
        mix_node.blend_type = 'MULTIPLY'
        mix_node.inputs['Fac'].default_value = 1.0
        mix_node.inputs['Color2'].default_value = (src.color.x, src.color.y,
                                                   src.color.z, src.color.w)
        links.new(mix_node.outputs[0], output_node.inputs[0])  # type: ignore
        if src.texture and src.texture.image:
            texture_node = nodes.new(type="ShaderNodeTexImage")
            nodes.active = texture_node
            texture_node.image = self._get_or_create_image(src.texture)
            links.new(texture_node.outputs[0],
                      mix_node.inputs[0])  # type: ignore

    def create_pbr(self, bl_material: bpy.types.Material,
                   src: pyscene.PBRMaterial):
        bl_material.use_nodes = True
        nodes: bpy.types.Nodes = bl_material.node_tree.nodes
        links: bpy.types.NodeLinks = bl_material.node_tree.links

        # clear nodes
        nodes.clear()

        # build node
        pos = NodePostion()
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        pos.increment(output_node)

        bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        pos.increment(bsdf_node)
        bsdf_node.location = (300, 0)
        bsdf_node.inputs['Base Color'].default_value = (src.color.x,
                                                        src.color.y,
                                                        src.color.z,
                                                        src.color.w)
        links.new(bsdf_node.outputs[0], output_node.inputs[0])  # type: ignore
        if src.texture and src.texture.image:
            texture_node = nodes.new(type="ShaderNodeTexImage")
            pos.increment(texture_node)
            nodes.active = texture_node
            texture_node.image = self._get_or_create_image(src.texture)
            links.new(texture_node.outputs[0],
                      bsdf_node.inputs[0])  # type: ignore
            links.new(texture_node.outputs[1],
                      bsdf_node.inputs['Alpha'])  # type: ignore
