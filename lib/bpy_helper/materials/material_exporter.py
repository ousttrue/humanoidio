from typing import List, Dict
import bpy, mathutils
from .. import pyscene
from . import pbr_material, mtoon_material


class MaterialExporter:
    def __init__(self):
        self.materials: List[pyscene.UnlitMaterial] = []
        self._material_map: Dict[bpy.types.Material, int] = {}

    def get_or_create_material(self,
                               m: bpy.types.Material) -> pyscene.UnlitMaterial:
        material_index = self._material_map.get(m)
        if isinstance(material_index, int):
            return self.materials[material_index]

        material = None
        for n in m.node_tree.nodes:
            if isinstance(n, bpy.types.ShaderNodeGroup):
                if n.node_tree.name == pbr_material.GltfPBR.GROUP_NAME:
                    material = pbr_material.export(m, n)
                    break

                if n.node_tree.name == mtoon_material.MToonGroup.GROUP_NAME:
                    material = mtoon_material.export(m, n)
                    break

        if isinstance(material, pyscene.UnlitMaterial):

            material_index = len(self.materials)
            self.materials.append(material)
            self._material_map[m] = material_index
            return material

        raise NotImplementedError()
