import ctypes
from typing import List
from . import glb


class Float3(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
    ]


class ExportMesh:
    def __init__(self, vertex_count: int, index_count: int):
        self.POSITION = (Float3 * vertex_count)()
        self.NORMAL = (Float3 * vertex_count)()
        self.indices = (ctypes.c_uint32 * index_count)()


class ExportScene:
    def __init__(self):
        self.meshes: List[ExportMesh] = []

    def to_glb(self):
        gltf = {}
        bin = b''
        return glb.to_glb(gltf, bin)
