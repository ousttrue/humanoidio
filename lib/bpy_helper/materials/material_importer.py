from logging import getLogger
logger = getLogger(__name__)
from typing import Dict, Any
import bpy, mathutils
from .. import pyscene
from .unlit_material_importer import build_unlit
from .pbr_material_importer import build_pbr
from .mtoon_material_importer import build_mtoon
from .texture_importer import TextureImporter


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
        bl_material.diffuse_color = (
            material.color.x,
            material.color.y,  # type: ignore
            material.color.z,
            material.color.w)
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

        if isinstance(material, pyscene.MToonMaterial):
            # MToon
            build_mtoon(bl_material, material, self.texture_importer)

        elif isinstance(material, pyscene.PBRMaterial):
            # PBR
            build_pbr(bl_material, material, self.texture_importer)

        else:
            # unlit
            build_unlit(bl_material, material, self.texture_importer)

        for n in bl_material.node_tree.nodes:
            n.select = False

        return bl_material
