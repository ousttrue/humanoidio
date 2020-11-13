from typing import NamedTuple, Dict, List
from .material import UnlitMaterial, Texture
from .submesh_mesh import SubmeshMesh
from .node import Node
from .. import formats


class IndexMap(NamedTuple):
    texture: Dict[int, Texture]
    material: Dict[int, UnlitMaterial]
    mesh: Dict[int, SubmeshMesh]
    node: Dict[int, Node]

    @staticmethod
    def create():
        return IndexMap({}, {}, {}, {})

    def get_nodes(self, indices: List[int]) -> List[Node]:
        return [self.node[i] for i in indices]

    def get_roots(self, gltf: formats.gltf.glTF) -> List[Node]:
        scene = gltf.scenes[gltf.scene if gltf.scene else 0]
        if not scene.nodes:
            return []
        return self.get_nodes(scene.nodes)
