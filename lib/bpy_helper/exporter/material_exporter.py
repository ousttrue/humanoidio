from typing import List, Dict
import bpy, mathutils
from ... import pyscene
from ..materials import pbr_material, mtoon_material
from .export_map import ExportMap


class MaterialExporter:
    def __init__(self, export_map: ExportMap):
        self.export_map = export_map

    def get_or_create_material(self,
                               m: bpy.types.Material) -> pyscene.UnlitMaterial:
        material_index = self.export_map._material_map.get(m)
        if isinstance(material_index, int):
            return self.export_map.materials[material_index]

        material = None
        for n in m.node_tree.nodes:
            if isinstance(n, bpy.types.ShaderNodeGroup):
                if n.node_tree.name == pbr_material.GltfPBR.GROUP_NAME:
                    material = pbr_material.export(m, n)
                    break

                if n.node_tree.name == mtoon_material.MToonGroup.GROUP_NAME:
                    material = mtoon_material.export(m, n)
                    break

        if material:

            material_index = len(self.export_map.materials)
            self.export_map.materials.append(material)
            self.export_map._material_map[m] = material_index
            return material

        raise NotImplementedError(f'fail to export {m}')
