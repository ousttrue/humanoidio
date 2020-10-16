import json
from typing import List

import bpy

from scene_translator.formats import gltf
from .import_manager import ImportManager
from . import blender_groupnode_io, gltf_pbr_node

from logging import getLogger  # pylint: disable=C0411
logger = getLogger(__name__)


def _create_material(manager: ImportManager,
                     material: gltf.Material) -> bpy.types.Material:
    blender_material = bpy.data.materials.new(material.name)
    # blender_material['js'] = json.dumps(material.js, indent=2)

    # blender_material.use_nodes = True
    # tree = blender_material.node_tree

    # tree.nodes.remove(tree.nodes['Principled BSDF'])

    # getLogger('').disabled = True
    # groups = blender_groupnode_io.import_groups(gltf_pbr_node.groups)
    # getLogger('').disabled = False

    # bsdf = tree.nodes.new('ShaderNodeGroup')
    # bsdf.node_tree = groups['glTF Metallic Roughness']

    # tree.links.new(bsdf.outputs['Shader'],
    #                tree.nodes['Material Output'].inputs['Surface'])

    # def create_image_node(texture_index: int):
    #     # uv => tex
    #     image_node = tree.nodes.new(type='ShaderNodeTexImage')
    #     image_node.image = manager.textures[texture_index]
    #     tree.links.new(
    #         tree.nodes.new('ShaderNodeTexCoord').outputs['UV'],
    #         image_node.inputs['Vector'])
    #     return image_node

    # def bsdf_link_image(texture_index: int, input_name: str):
    #     texture = create_image_node(texture_index)
    #     tree.links.new(texture.outputs["Color"], bsdf.inputs[input_name])

    # if material.normalTexture:
    #     bsdf_link_image(material.normalTexture.index, 'Normal')

    # if material.occlusionTexture:
    #     bsdf_link_image(material.occlusionTexture.index, 'Occlusion')

    # if material.emissiveTexture:
    #     bsdf_link_image(material.emissiveTexture.index, 'Emissive')

    # pbr = material.pbrMetallicRoughness
    # if pbr:
    #     if pbr.baseColorTexture and pbr.baseColorFactor:
    #         # mix
    #         mix = tree.nodes.new(type='ShaderNodeMixRGB')
    #         mix.blend_type = 'MULTIPLY'
    #         mix.inputs[2].default_value = pbr.baseColorFactor

    #     elif pbr.baseColorTexture:
    #         bsdf_link_image(pbr.baseColorTexture.index, 'BaseColor')
    #     else:
    #         # factor
    #         pass

    #     if pbr.metallicRoughnessTexture:
    #         bsdf_link_image(pbr.metallicRoughnessTexture.index,
    #                         'MetallicRoughness')

    # progress.step()
    return blender_material


def load_materials(manager: ImportManager) -> List[bpy.types.Material]:

    materials = [
        _create_material(manager, material)
        for material in manager.gltf.materials
    ]
    return materials
