from typing import Dict, List, Callable, Tuple, Any
import PIL.Image
import PIL.ImageOps
import bpy, mathutils
from .. import pyscene


class NodeTree:
    def __init__(self, bl_material: bpy.types.Material, x=0, y=0):
        self.x = x
        self.y = y

        bl_material.use_nodes = True
        self.nodes: bpy.types.Nodes = bl_material.node_tree.nodes
        self.links: bpy.types.NodeLinks = bl_material.node_tree.links
        # clear nodes
        self.nodes.clear()

    def _create_node(self, name: str) -> Any:
        if not name.startswith("ShaderNode"):
            name = "ShaderNode" + name
        node = self.nodes.new(type=name)
        node.location = (self.x, self.y)
        self.x -= 200
        return node

    def _create_texture_node(self, label: str, image: bpy.types.Image,
                             is_opaque: bool, input_color, input_alpha):
        texture_node = self._create_node("ShaderNodeTexImage")
        # self.nodes.active = texture_node
        texture_node.label = label
        texture_node.image = image
        self.links.new(texture_node.outputs[0], input_color)  # type: ignore
        if is_opaque:
            # alpha を強制的に 1 にする
            math_node = self._create_node("Math")
            math_node.operation = 'MAXIMUM'
            math_node.inputs[1].default_value = 1.0
            self.links.new(
                texture_node.outputs[1],  # type: ignore
                math_node.inputs[0])  # type: ingore

            self.links.new(math_node.outputs[0], input_alpha)  # type: ignore
        else:
            self.links.new(texture_node.outputs[1],
                           input_alpha)  # type: ignore

    def create_unlit(self, src: pyscene.Material,
                     get_or_create_image: Callable[[pyscene.Texture],
                                                   bpy.types.Image]):
        output_node = self._create_node("ShaderNodeOutputMaterial")

        # build node
        mix_node = self._create_node("ShaderNodeMixShader")
        transparent = self._create_node("ShaderNodeBsdfTransparent")
        self.links.new(transparent.outputs[0],
                       mix_node.inputs[1])  # type: ignore

        if src.texture and src.texture.image:
            self._create_texture_node(
                'BaseColor', get_or_create_image(src.texture),
                src.blend_mode == pyscene.BlendMode.Opaque, mix_node.inputs[2],
                mix_node.inputs[0])

    def create_pbr(self, src: pyscene.PBRMaterial,
                   get_or_create_image: Callable[[pyscene.Texture],
                                                 bpy.types.Image]):
        # build node
        output_node = self._create_node("ShaderNodeOutputMaterial")
        bsdf_node = self._create_node("ShaderNodeBsdfPrincipled")
        bsdf_node.inputs['Base Color'].default_value = (src.color.x,
                                                        src.color.y,
                                                        src.color.z,
                                                        src.color.w)
        self.links.new(bsdf_node.outputs[0],
                       output_node.inputs[0])  # type: ignore
        if src.texture and src.texture.image:
            self._create_texture_node(
                'BaseColor', get_or_create_image(src.texture),
                src.blend_mode == pyscene.BlendMode.Opaque,
                bsdf_node.inputs[0], bsdf_node.inputs['Alpha'])


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

        tree = NodeTree(bl_material)
        if isinstance(material, pyscene.PBRMaterial):
            # PBR
            tree.create_pbr(material, self._get_or_create_image)
        else:
            # unlit
            tree.create_unlit(material, self._get_or_create_image)

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
