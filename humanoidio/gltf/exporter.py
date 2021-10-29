from typing import List, Dict, Any, NamedTuple
from . import accessor_util
from .node import Node
from .mesh import ExportMesh
from . import glb
from enum import Enum, auto


class AnimationChannelTargetPath(Enum):
    translation = auto()
    rotation = auto()
    scale = auto()
    weights = auto()


class Animation(NamedTuple):
    node: int
    target_path: AnimationChannelTargetPath
    times: List[float]
    values: List[Any]


class GltfWriter:
    def __init__(self):
        self.gltf = {
            'asset': {
                'version': '2.0',
            },
            'buffers': [],
            'bufferViews': [],
            'accessors': [],
            'meshes': [],
            'nodes': [],
            'scenes': [],
        }
        self.accessor = accessor_util.GltfAccessor(self.gltf, bytearray())

    def push_mesh(self, mesh: ExportMesh):
        gltf_mesh = {'primitives': []}
        primitive: Dict[str, Any] = {'attributes': {}}
        primitive['attributes']['POSITION'] = self.accessor.push_array(
            mesh.POSITION, True)
        primitive['attributes']['NORMAL'] = self.accessor.push_array(
            mesh.NORMAL)
        primitive['indices'] = self.accessor.push_array(mesh.indices)
        gltf_mesh['primitives'].append(primitive)

        mesh_index = len(self.gltf['meshes'])
        self.gltf['meshes'].append(gltf_mesh)

        return mesh_index

    def _export_node(self, node: Node):
        gltf_node: Dict[str, Any] = {'name': node.name}
        node_index = len(self.gltf['nodes'])
        self.gltf['nodes'].append(gltf_node)

        # TODO: TRS

        # mesh
        if isinstance(node.mesh, ExportMesh):
            mesh_index = self.push_mesh(node.mesh)
            gltf_node['mesh'] = mesh_index

        # children
        for child in node.children:
            child_node_index = self._export_node(child)
            if 'children' not in gltf_node:
                gltf_node['children'] = []
            gltf_node['children'].append(child_node_index)

        return node_index

    def push_scene(self, nodes: List[Node]):
        scene = {'nodes': []}
        for node in nodes:
            node_index = self._export_node(node)
            scene['nodes'].append(node_index)
        self.gltf['scenes'].append(scene)

    def push_animation(self, name: str, animation: Animation):
        if 'animations' not in self.gltf:
            self.gltf['animations'] = []

        gltf_animation = {
            "name":
            name,
            "samplers": [{
                "input": 0,
                "interpolation": "LINEAR",
                "output": 1
            }],
            "channels": [{
                "sampler": 0,
                "target": {
                    "node": 0,
                    "path": "rotation"
                }
            }],
        }
        self.gltf['animations'].append(gltf_animation)

    def to_gltf(self):
        self.gltf['buffers'] = [{'byteLength': len(self.accessor.bin)}]
        return self.gltf, bytes(self.accessor.bin)

    def to_glb(self) -> bytes:
        gltf, bin = self.to_gltf()
        return glb.to_glb(gltf, bin)
