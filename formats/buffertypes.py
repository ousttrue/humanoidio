from typing import Iterable, List, Dict, Tuple
import ctypes
import mathutils


class Vector2(ctypes.LittleEndianStructure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]

    @staticmethod
    def from_faceUV(uv: mathutils.Vector) -> 'Vector2':
        return Vector2(uv.x, -uv.y)


class Vector3(ctypes.LittleEndianStructure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float),
                ("z", ctypes.c_float)]

    @staticmethod
    def from_Vector(v: mathutils.Vector) -> 'Vector3':
        # return Vector3(v.x, v.z, -v.y)
        return Vector3(-v.x, v.z, v.y)

    def __repr__(self) -> str:
        return f'({self.x}, {self.y}, {self.z})'

    def __sub__(self, rhs):
        return Vector3(self.x - rhs.x, self.y - rhs.y, self.z - rhs.z)

    def __add__(self, rhs):
        return Vector3(self.x + rhs.x, self.y + rhs.y, self.z + rhs.z)


def get_min_max2(list: Iterable[Vector2]):
    min: List[float] = [float('inf')] * 2
    max: List[float] = [float('-inf')] * 2
    for v in list:
        if v.x < min[0]:
            min[0] = v.x
        if v.x > max[0]:
            max[0] = v.x
        if v.y < min[1]:
            min[1] = v.y
        if v.y > max[1]:
            max[1] = v.y
    return min, max


class Matrix4(ctypes.LittleEndianStructure):
    _fields_ = [
        ("_11", ctypes.c_float),
        ("_12", ctypes.c_float),
        ("_13", ctypes.c_float),
        ("_14", ctypes.c_float),
        ("_21", ctypes.c_float),
        ("_22", ctypes.c_float),
        ("_23", ctypes.c_float),
        ("_24", ctypes.c_float),
        ("_31", ctypes.c_float),
        ("_32", ctypes.c_float),
        ("_33", ctypes.c_float),
        ("_34", ctypes.c_float),
        ("_41", ctypes.c_float),
        ("_42", ctypes.c_float),
        ("_43", ctypes.c_float),
        ("_44", ctypes.c_float),
    ]

    @staticmethod
    def identity() -> 'Matrix4':
        return Matrix4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0,
                       0.0, 0.0, 0.0, 0.0, 1.0)

    @staticmethod
    def translation(x: float, y: float, z: float) -> 'Matrix4':
        return Matrix4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0,
                       0.0, x, y, z, 1.0)


class Vector4(ctypes.LittleEndianStructure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float),
                ("z", ctypes.c_float), ("w", ctypes.c_float)]

    def __mul__(self, factor: float) -> 'Vector4':
        return Vector4(self.x * factor, self.y * factor, self.z * factor,
                       self.w * factor)


class IVector4(ctypes.LittleEndianStructure):
    _fields_ = [("x", ctypes.c_ushort), ("y", ctypes.c_ushort),
                ("z", ctypes.c_ushort), ("w", ctypes.c_ushort)]


class BoneWeight(ctypes.LittleEndianStructure):
    _fields_ = [
        ("i0", ctypes.c_int),
        ("i1", ctypes.c_int),
        ("i2", ctypes.c_int),
        ("i3", ctypes.c_int),
        ("weights", Vector4),
    ]

    def push(self, i: int, w: float):
        if self.weights.x == 0:
            self.i0 = i
            self.weights.x = w
        elif self.weights.y == 0:
            self.i1 = i
            self.weights.y = w
        elif self.weights.z == 0:
            self.i2 = i
            self.weights.z = w
        elif self.weights.w == 0:
            self.i3 = i
            self.weights.w = w
        else:
            raise NotImplementedError('over 4')

    def to_joints_with_weights(self, group_index_to_joint_index: Dict[int, int]
                               ) -> Tuple[IVector4, Vector4]:
        '''
        ついでに正規化する
        '''
        total_weights = (self.weights.x + self.weights.y + self.weights.z +
                         self.weights.w)
        factor = 1 / total_weights

        joints = IVector4(
            group_index_to_joint_index[self.i0]
            if self.i0 in group_index_to_joint_index else 0,
            group_index_to_joint_index[self.i1]
            if self.i1 in group_index_to_joint_index else 0,
            group_index_to_joint_index[self.i2]
            if self.i2 in group_index_to_joint_index else 0,
            group_index_to_joint_index[self.i3]
            if self.i3 in group_index_to_joint_index else 0)

        weights = self.weights * factor

        return (joints, weights)
