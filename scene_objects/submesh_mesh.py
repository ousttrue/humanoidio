from typing import Any, List, Optional, Dict
import array
import bpy


class Submesh:
    def __init__(self, material: bpy.types.Material) -> None:
        self.indices: Any = array.array('I')
        self.material = material


class SubmeshMesh:
    def __init__(self, name: str):
        self.name = name
        self.submesh_map: Dict[int, Submesh] = {}
        self.submeshes: List[Submesh] = []
        self.vertex_count = 0
        # attributes
        self.positions: Optional[memoryview] = None  # float3
        self.normals: Optional[memoryview] = None  # float3
        self.texcoord: Optional[memoryview] = None  # float2
        self.joints: Optional[memoryview] = None  # int4
        self.weights: Optional[memoryview] = None  # float4
        # morph
        self.morph_map: Dict[str, memoryview] = {}

    def __str__(self) -> str:
        return f'<SubmeshMesh: {self.vertex_count}verts>'

    def get_or_create_submesh(self, material_index: int,
                              materials: List[bpy.types.Material]) -> Submesh:
        if material_index in self.submesh_map:
            return self.submesh_map[material_index]

        if material_index < len(materials):
            material = materials[material_index]
        else:
            # default material
            material = bpy.data.materials[0]
        submesh = Submesh(material)
        self.submeshes.append(submesh)
        self.submesh_map[material_index] = submesh
        return submesh
