from typing import Union
import ctypes


class Float2(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
    ]


class Float3(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
    ]
    __match_args__ = ('x', 'y', 'z')

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __mul__(self, rhs: Union[float, 'Float3']) -> 'Float3':
        match rhs:
            case float() as n:
                return Float3(self.x * rhs, self.y * rhs, self.z * rhs)
            case Float3(x, y, z):
                return Float3(self.x * x, self.y * y, self.z * z)
            case _:
                raise NotImplementedError()

    def __add__(self, rhs: 'Float3') -> 'Float3':
        return Float3(self.x + rhs.x, self.y + rhs.y, self.z+rhs.z)

    def reverse_z(self) -> 'Float3':
        return Float3(self.x, self.y, -self.z)

    def rotate_y180(self) -> 'Float3':
        # -x and -z
        return Float3(-self.x, self.y, -self.z)


class Float4(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('w', ctypes.c_float),
    ]


class Mat4(ctypes.Structure):
    _fields_ = [
        ('_11', ctypes.c_float),
        ('_12', ctypes.c_float),
        ('_13', ctypes.c_float),
        ('_14', ctypes.c_float),
        ('_21', ctypes.c_float),
        ('_22', ctypes.c_float),
        ('_23', ctypes.c_float),
        ('_24', ctypes.c_float),
        ('_31', ctypes.c_float),
        ('_32', ctypes.c_float),
        ('_33', ctypes.c_float),
        ('_34', ctypes.c_float),
        ('_41', ctypes.c_float),
        ('_42', ctypes.c_float),
        ('_43', ctypes.c_float),
        ('_44', ctypes.c_float),
    ]

    def __iter__(self):
        yield self._11
        yield self._12
        yield self._13
        yield self._14
        yield self._21
        yield self._22
        yield self._23
        yield self._24
        yield self._31
        yield self._32
        yield self._33
        yield self._34
        yield self._41
        yield self._42
        yield self._43
        yield self._44


class UShort4(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_uint16),
        ('y', ctypes.c_uint16),
        ('z', ctypes.c_uint16),
        ('w', ctypes.c_uint16),
    ]


class RenderVertex(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('position', Float3),
        ('normal', Float3),
        ('uv', Float2),
    ]


class Vertex4BoneWeights(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('position', Float3),
        ('normal', Float3),
        ('uv', Float2),
        ('bone', Float4),
        ('weight', Float4),
    ]
