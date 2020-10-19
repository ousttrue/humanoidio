from typing import Any, List, Optional, Dict
import array
import bpy


class Submesh:
    def __init__(self, material: Optional[bpy.types.Material]) -> None:
        self.indices: Any = array.array('I')
        self.material = material


class SubmeshMesh:
    def __init__(self, name: str, positions: Optional[memoryview] = None):
        self.name = name
        self.submeshes: List[Submesh] = []
        self.vertex_count = len(positions.tobytes()) // 12 if positions else 0
        # attributes
        self.positions = positions
        self.normals: Optional[memoryview] = None  # float3
        self.texcoord: Optional[memoryview] = None  # float2
        self.joints: Optional[memoryview] = None  # int4
        self.weights: Optional[memoryview] = None  # float4
        # morph
        self.morph_map: Dict[str, memoryview] = {}
        # materials
        self.textures: List[bpy.types.Texture] = []

    def __str__(self) -> str:
        return f'<SubmeshMesh: {self.vertex_count}verts>'
