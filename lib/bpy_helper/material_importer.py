from logging import getLogger
logger = getLogger(__name__)
import pathlib
import tempfile
from typing import Dict, List, Callable, Tuple, Any
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

    def create_unlit(self, src: pyscene.Material,
                     get_or_create_image: Callable[[pyscene.Texture],
                                                   bpy.types.Image]):
        '''
        Unlit(texture color without shading)
        '''
        output_node = self._create_node("OutputMaterial")

        # build node
        mix_node = self._create_node("MixShader")
        self.links.new(mix_node.outputs[0],
                       output_node.inputs[0])  # type: ignore

        transparent = self._create_node("BsdfTransparent")
        self.links.new(transparent.outputs[0],
                       mix_node.inputs[1])  # type: ignore

        if src.texture:
            self._create_texture_node(
                'ColorTexture', get_or_create_image(src.texture),
                src.blend_mode == pyscene.BlendMode.Opaque, mix_node.inputs[2],
                mix_node.inputs[0])

    def create_pbr(self, src: pyscene.PBRMaterial,
                   get_or_create_image: Callable[[pyscene.Texture],
                                                 bpy.types.Image]):
        '''
        BsdfPrincipled
        '''
        # build node
        output_node = self._create_node("OutputMaterial")
        bsdf_node = self._create_node("BsdfPrincipled")
        bsdf_node.inputs['Base Color'].default_value = (src.color.x,
                                                        src.color.y,
                                                        src.color.z,
                                                        src.color.w)
        self.links.new(bsdf_node.outputs[0],
                       output_node.inputs[0])  # type: ignore

        if src.texture:
            # color texture
            self._create_texture_node(
                'ColorTexture', get_or_create_image(src.texture),
                src.blend_mode == pyscene.BlendMode.Opaque,
                bsdf_node.inputs[0], bsdf_node.inputs['Alpha'])

        if src.normal_map:
            # normal map
            normal_texture_node = self._create_node("TexImage")
            normal_texture_node.label = 'NormalTexture'
            normal_image = get_or_create_image(src.normal_map)  # type: ignore
            normal_texture_node.image = normal_image

            normal_map = self._create_node("NormalMap")
            self.links.new(normal_texture_node.outputs[0],
                           normal_map.inputs[1])  # type: ignore
            self.links.new(normal_map.outputs[0],
                           bsdf_node.inputs['Normal'])  # type: ignore

        if src.emissive_texture:
            self._create_texture_node(
                'EmissiveTexture', get_or_create_image(src.emissive_texture),
                False, bsdf_node.inputs['Emission'], None)

        if src.metallic_roughness_texture:
            separate_node = self._create_node("SeparateRGB")
            self.links.new(separate_node.outputs['G'],
                           bsdf_node.inputs['Roughness'])  # type: ignore
            self.links.new(separate_node.outputs['B'],
                           bsdf_node.inputs['Metallic'])  # type: ignore
            self._create_texture_node(
                'MetallicRoughness',
                get_or_create_image(src.metallic_roughness_texture), False,
                separate_node.inputs[0], None)

        if src.occlusion_texture:
            pass


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

        logger.debug(f'create {texture}')

        if isinstance(texture.url_or_bytes, pathlib.Path):
            path = texture.url_or_bytes.absolute()
            bl_image = bpy.data.images.load(str(path))

        elif isinstance(texture.url_or_bytes, bytes):
            # Image stored as data => create a tempfile, pack, and delete file
            # img_from_file = False
            img_data = texture.url_or_bytes
            # img_name = img_name or 'Image_%d' % img_idx
            tmp_dir = tempfile.TemporaryDirectory(prefix='gltfimg-')
            # filename = _filenamify(img_name) or 'Image_%d' % img_idx
            # filename += _img_extension(img)
            path = pathlib.Path(tmp_dir.name) / texture.name
            with open(path, 'wb') as f:
                f.write(img_data)
            bl_image = bpy.data.images.load(str(path))
            bl_image.pack()

        else:
            raise Exception()

        bl_image.colorspace_settings.is_data = texture.is_data
        bl_image.name = texture.name

        self.image_map[texture] = bl_image
        return bl_image
