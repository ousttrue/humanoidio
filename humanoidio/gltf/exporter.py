import ctypes
from typing import List, Dict, Any
from . import glb
from . import accessor_util
from .types import Float3


class ExportMesh:
    def __init__(self, vertex_count: int, index_count: int):
        self.POSITION = (Float3 * vertex_count)()
        self.NORMAL = (Float3 * vertex_count)()
        self.indices = (ctypes.c_uint32 * index_count)()


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
        }
        self.accessor = accessor_util.GltfAccessor(self.gltf, bytearray())

    def push_mesh(self, mesh: ExportMesh):
        gltf_mesh = {'primitives': []}
        primitive: Dict[str, Any] = {'attributes': {}}
        primitive['attributes']['POSITION'] = self.accessor.push_array(
            mesh.POSITION)
        primitive['attributes']['NORMAL'] = self.accessor.push_array(
            mesh.NORMAL)
        primitive['indices'] = self.accessor.push_array(mesh.indices)
        gltf_mesh['primitives'].append(primitive)
        mesh_index = len(self.gltf['meshes'])
        self.gltf['meshes'].append(gltf_mesh)

        # TODO:
        node = {'mesh': mesh_index}
        self.gltf['nodes'].append(node)

        return mesh_index

    def to_gltf(self):
        self.gltf['buffers'] = [{'byteLength': len(self.accessor.bin)}]
        return self.gltf, bytes(self.accessor.bin)


class ExportScene:
    def __init__(self):
        self.meshes: List[ExportMesh] = []

    def to_glb(self):
        writer = GltfWriter()
        for mesh in self.meshes:
            writer.push_mesh(mesh)
        gltf, bin = writer.to_gltf()

        return glb.to_glb(gltf, bin)
