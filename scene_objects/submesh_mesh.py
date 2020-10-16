from typing import NamedTuple, Any, List, Optional, Dict
import array
import bpy


class Submesh:
    def __init__(self, material: bpy.types.Material) -> None:
        self.indices: Any = array.array('I')
        self.material = material


class SubmeshMesh(NamedTuple):
    name: str
    total_vertex_count: int
    submeshes: List[Submesh]
    # attributes
    positions: memoryview  # float3
    normals: memoryview  # float3
    uvs: Optional[memoryview]  # float2
    joints: Optional[memoryview]  # int4
    weights: Optional[memoryview]  # float4
    # morph
    morph_map: Dict[str, memoryview] = {}
