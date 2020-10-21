from typing import Dict, List
import bpy, mathutils
from .. import pyscene

# def _create_texture(manager: 'ImportManager', index: int,
#                     texture: gltf.Texture) -> bpy.types.Texture:
#     image = manager.gltf.images[texture.source]
#     if image.uri:
#         texture = load_image(image.uri, str(manager.base_dir))
#     elif image.bufferView != -1:
#         if not bpy.data.filepath:
#             # can not extract image files
#             #raise Exception('no bpy.data.filepath')
#             texture = bpy.data.images.new('image', 128, 128)

#         else:

#             image_dir = pathlib.Path(
#                 bpy.data.filepath).absolute().parent / manager.path.stem
#             if not image_dir.exists():
#                 image_dir.mkdir()

#             data = manager.get_view_bytes(image.bufferView)
#             image_path = image_dir / f'texture_{index:0>2}.png'
#             if not image_path.exists():
#                 with image_path.open('wb') as w:
#                     w.write(data)

#             texture = load_image(image_path.name, str(image_path.parent))
#     else:
#         raise Exception("invalid image")
#     progress.step()
#     return texture

# def _create_material(manager: 'ImportManager',
#                      material: gltf.Material) -> bpy.types.Material:
#     blender_material = bpy.data.materials.new(material.name)
#     # blender_material['js'] = json.dumps(material.js, indent=2)

#     # blender_material.use_nodes = True
#     # tree = blender_material.node_tree

#     # tree.nodes.remove(tree.nodes['Principled BSDF'])

#     # getLogger('').disabled = True
#     # groups = blender_groupnode_io.import_groups(gltf_pbr_node.groups)
#     # getLogger('').disabled = False

#     # bsdf = tree.nodes.new('ShaderNodeGroup')
#     # bsdf.node_tree = groups['glTF Metallic Roughness']

#     # tree.links.new(bsdf.outputs['Shader'],
#     #                tree.nodes['Material Output'].inputs['Surface'])

#     # def create_image_node(texture_index: int):
#     #     # uv => tex
#     #     image_node = tree.nodes.new(type='ShaderNodeTexImage')
#     #     image_node.image = manager.textures[texture_index]
#     #     tree.links.new(
#     #         tree.nodes.new('ShaderNodeTexCoord').outputs['UV'],
#     #         image_node.inputs['Vector'])
#     #     return image_node

#     # def bsdf_link_image(texture_index: int, input_name: str):
#     #     texture = create_image_node(texture_index)
#     #     tree.links.new(texture.outputs["Color"], bsdf.inputs[input_name])

#     # if material.normalTexture:
#     #     bsdf_link_image(material.normalTexture.index, 'Normal')

#     # if material.occlusionTexture:
#     #     bsdf_link_image(material.occlusionTexture.index, 'Occlusion')

#     # if material.emissiveTexture:
#     #     bsdf_link_image(material.emissiveTexture.index, 'Emissive')

#     # pbr = material.pbrMetallicRoughness
#     # if pbr:
#     #     if pbr.baseColorTexture and pbr.baseColorFactor:
#     #         # mix
#     #         mix = tree.nodes.new(type='ShaderNodeMixRGB')
#     #         mix.blend_type = 'MULTIPLY'
#     #         mix.inputs[2].default_value = pbr.baseColorFactor

#     #     elif pbr.baseColorTexture:
#     #         bsdf_link_image(pbr.baseColorTexture.index, 'BaseColor')
#     #     else:
#     #         # factor
#     #         pass

#     #     if pbr.metallicRoughnessTexture:
#     #         bsdf_link_image(pbr.metallicRoughnessTexture.index,
#     #                         'MetallicRoughness')

#     # progress.step()
#     return blender_material


class MaterialImporter:
    def __init__(self):
        self.material_map: Dict[pyscene.Material, bpy.types.Material] = {}
        self.image_map: Dict[pyscene.Texture, bpy.types.Image] = {}

    def get_or_create_material(
            self, material: pyscene.Material) -> bpy.types.Material:
        bl_material = self.material_map.get(material)
        if bl_material:
            return bl_material

        bl_material = bpy.data.materials.new(material.name)
        self.material_map[material] = bl_material

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
        bl_image = bpy.data.images.new(texture.name,
                                       width=image.width,
                                       height=image.height)
        self.image_map[texture] = bl_image
        return bl_image

    def create_unlit(self, bl_material: bpy.types.Material,
                     src: pyscene.Material):
        raise NotImplementedError()

    def create_pbr(self, bl_material: bpy.types.Material,
                   src: pyscene.PBRMaterial):
        bl_material.use_nodes = True
        nodes: bpy.types.Nodes = bl_material.node_tree.nodes
        links: bpy.types.NodeLinks = bl_material.node_tree.links

        # clear nodes
        nodes.clear()

        # build node
        bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        links.new(bsdf_node.outputs[0], output_node.inputs[0])  # type: ignore
        if src.texture and src.texture.image:
            texture_node = nodes.new(type="ShaderNodeTexImage")
            nodes.active = texture_node
            texture_node.image = self._get_or_create_image(src.texture)
            links.new(texture_node.outputs[0],
                      bsdf_node.inputs[0])  # type: ignore
