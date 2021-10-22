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
            'buffers': [],
            'bufferViews': [],
            'accessors': [],
            'meshes': [],
            'nodes': [],
        }
        self.bin = bytearray()

    def push_bytes(self, data: bytes):
        bufferView_index = len(self.gltf['bufferViews'])
        bufferView = {
            'buffer': 0,
            'byteOffset': len(self.bin),
            'byteLength': len(data),
        }
        self.bin.extend(data)
        self.gltf['bufferViews'].append(bufferView)
        return bufferView_index

    def push_array(self, values) -> int:
        accessor_index = len(self.gltf['accessors'])
        t, c = accessor_util.get_type_count(values)
        accessor = {
            'bufferView': self.push_bytes(memoryview(values).cast('B')),
            'type': t,
            'componentType': c,
        }
        self.gltf['accessors'].append(accessor)
        return accessor_index

    def push_mesh(self, mesh: ExportMesh):
        gltf_mesh = {'primitives': []}
        primitive: Dict[str, Any] = {'attributes': {}}
        primitive['attributes']['POSITION'] = self.push_array(mesh.POSITION)
        primitive['attributes']['NORMAL'] = self.push_array(mesh.NORMAL)
        primitive['indices'] = self.push_array(mesh.indices)
        gltf_mesh['primitives'].append(primitive)
        mesh_index = len(self.gltf['meshes'])
        self.gltf['meshes'].append(gltf_mesh)

        # TODO:
        node = {'mesh': mesh_index}
        self.gltf['nodes'].append(node)

        return mesh_index

    def to_gltf(self):
        self.gltf['buffers'] = [{'byteLength': len(self.bin)}]
        return self.gltf, bytes(self.bin)


class ExportScene:
    def __init__(self):
        self.meshes: List[ExportMesh] = []

    def to_glb(self):
        writer = GltfWriter()
        for mesh in self.meshes:
            writer.push_mesh(mesh)
        gltf, bin = writer.to_gltf()

        return glb.to_glb(gltf, bin)
