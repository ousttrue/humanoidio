from typing import Dict, List, Optional
from .. import formats
from .submesh_mesh import SubmeshMesh
from .node import Node


class IndexMap:
    def __init__(self, gltf: formats.gltf.glTF):
        from .material import UnlitMaterial, Texture
        from .vrm_loader import Vrm
        self.gltf = gltf
        self.texture: Dict[int, Texture] = {}
        self.material: Dict[int, UnlitMaterial] = {}
        self.mesh: Dict[int, SubmeshMesh] = {}
        self.node: Dict[int, Node] = {}
        self.vrm: Optional[Vrm] = None

    def load_vrm(self):
        from .vrm_loader import Vrm
        self.vrm = Vrm.load(self, self.gltf)

    def get_nodes(self, indices: List[int]) -> List[Node]:
        return [self.node[i] for i in indices]

    def get_roots(self) -> List[Node]:
        scene = self.gltf.scenes[self.gltf.scene if self.gltf.scene else 0]
        if not scene.nodes:
            return []
        return self.get_nodes(scene.nodes)

    def node_from_mesh(self, mesh: SubmeshMesh) -> Optional[Node]:
        for node in self.node.values():
            if node.mesh == mesh:
                return node
