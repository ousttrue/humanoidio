from logging import getLogger
logger = getLogger(__name__)
from typing import NamedTuple, MutableSequence
import ctypes


class Float2(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]


class Float3(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float),
                ("z", ctypes.c_float)]


class Float4(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("w", ctypes.c_float),
    ]

    def __getitem__(self, i: int) -> float:
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        elif i == 2:
            return self.z
        elif i == 3:
            return self.w
        else:
            raise IndexError()


class Mat16(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("f00", ctypes.c_float),
        ("f01", ctypes.c_float),
        ("f02", ctypes.c_float),
        ("f03", ctypes.c_float),
        ("f10", ctypes.c_float),
        ("f11", ctypes.c_float),
        ("f12", ctypes.c_float),
        ("f13", ctypes.c_float),
        ("f20", ctypes.c_float),
        ("f21", ctypes.c_float),
        ("f22", ctypes.c_float),
        ("f23", ctypes.c_float),
        ("f30", ctypes.c_float),
        ("f31", ctypes.c_float),
        ("f32", ctypes.c_float),
        ("f33", ctypes.c_float),
    ]


class UShort4(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("x", ctypes.c_ushort),
        ("y", ctypes.c_ushort),
        ("z", ctypes.c_ushort),
        ("w", ctypes.c_ushort),
    ]

    def __getitem__(self, i: int) -> int:
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        elif i == 2:
            return self.z
        elif i == 3:
            return self.w
        else:
            raise IndexError()


class PlanarBuffer(NamedTuple):
    position: MutableSequence[Float3]
    normal: MutableSequence[Float3]
    texcoord: MutableSequence[Float2]
    joints: MutableSequence[UShort4]
    weights: MutableSequence[Float4]

    def get_vertex_count(self) -> int:
        return len(self.position)

    @staticmethod
    def create(vertex_count: int) -> 'PlanarBuffer':
        pos = (Float3 * vertex_count)()
        nom = (Float3 * vertex_count)()
        uv = (Float2 * vertex_count)()
        joints = (UShort4 * vertex_count)()
        weights = (Float4 * vertex_count)()
        return PlanarBuffer(pos, nom, uv, joints, weights)  # type: ignore
