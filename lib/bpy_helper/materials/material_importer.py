from logging import getLogger
logger = getLogger(__name__)
from typing import Dict, Any
import bpy, mathutils
from .. import pyscene
from .unlit_material_importer import build_unlit
from .pbr_material_importer import build_pbr
from .texture_importer import TextureImporter


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
        texture_node = self._create_node("TexImage")
        # self.nodes.active = texture_node
        texture_node.label = label
        texture_node.image = image
        self.links.new(texture_node.outputs[0], input_color)  # type: ignore

        # alpha blending
        if input_alpha:
            if is_opaque:
                # alpha を強制的に 1 にする
                math_node = self._create_node("Math")
                math_node.operation = 'MAXIMUM'
                math_node.inputs[1].default_value = 1.0
                self.links.new(
                    texture_node.outputs[1],  # type: ignore
                    math_node.inputs[0])  # type: ingore

                self.links.new(math_node.outputs[0],
                               input_alpha)  # type: ignore
            else:
                self.links.new(texture_node.outputs[1],
                               input_alpha)  # type: ignore

    def create_mtoon(self, src: pyscene.MToonMaterial,
                     texture_importer: TextureImporter):
        '''
        BsdfPrincipled
        '''
        # build node
        output_node = self._create_node("OutputMaterial")
        bsdf_node = self._create_node("BsdfPrincipled")
        bsdf_node.inputs['Roughness'].default_value = 1
        bsdf_node.inputs['Specular'].default_value = 0
        bsdf_node.inputs['Base Color'].default_value = (src.color.x,
                                                        src.color.y,
                                                        src.color.z,
                                                        src.color.w)
        self.links.new(bsdf_node.outputs[0],
                       output_node.inputs[0])  # type: ignore

        if src.color_texture:
            # color texture
            self._create_texture_node(
                'ColorTexture',
                texture_importer.get_or_create_image(src.color_texture),
                src.blend_mode == pyscene.BlendMode.Opaque,
                bsdf_node.inputs[0], bsdf_node.inputs['Alpha'])

        if src.normal_texture:
            # normal map
            normal_texture_node = self._create_node("TexImage")
            normal_texture_node.label = 'NormalTexture'
            normal_image = texture_importer.get_or_create_image(
                src.normal_texture)  # type: ignore
            normal_texture_node.image = normal_image

            normal_map = self._create_node("NormalMap")
            self.links.new(normal_texture_node.outputs[0],
                           normal_map.inputs[1])  # type: ignore
            self.links.new(normal_map.outputs[0],
                           bsdf_node.inputs['Normal'])  # type: ignore

        if src.emissive_texture:
            self._create_texture_node(
                'EmissiveTexture',
                texture_importer.get_or_create_image(src.emissive_texture),
                False, bsdf_node.inputs['Emission'], None)


class MaterialImporter:
    def __init__(self):
        self.material_map: Dict[pyscene.UnlitMaterial, bpy.types.Material] = {}
        self.texture_importer = TextureImporter()

    def get_or_create_material(
            self, material: pyscene.UnlitMaterial) -> bpy.types.Material:
        if material in self.material_map:
            return self.material_map[material]

        # base color
        logger.debug(f'create: {material}')

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

        bl_material.use_nodes = True
        bl_material.node_tree.nodes.clear()

        tree = NodeTree(bl_material)
        if isinstance(material, pyscene.MToonMaterial):
            # MToon
            tree.create_mtoon(material, self.texture_importer)
        elif isinstance(material, pyscene.PBRMaterial):
            # PBR
            build_pbr(bl_material, material, self.texture_importer)
        else:
            # unlit
            # tree.create_unlit(material, self._get_or_create_image)
            build_unlit(bl_material, material, self.texture_importer)

        for n in bl_material.node_tree.nodes:
            n.select = False

        return bl_material
