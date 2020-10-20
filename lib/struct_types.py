from logging import getLogger
logger = getLogger(__name__)
from typing import NamedTuple, MutableSequence, Dict, Tuple, Iterable, List
import ctypes
import bpy, mathutils


class Float2(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]

    @staticmethod
    def from_faceUV(uv: mathutils.Vector) -> 'Float2':
        return Float2(uv.x, -uv.y)

    def __hash__(self):
        return hash(self.x)

    def __eq__(self, other: 'Float2') -> bool:
        if self.x != other.x: return False
        if self.y != other.y: return False
        return True


class Float3(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float),
                ("z", ctypes.c_float)]

    @staticmethod
    def from_Vector(v: mathutils.Vector) -> 'Float3':
        # return Float3(v.x, v.z, -v.y)
        return Float3(-v.x, v.z, v.y)

    def __hash__(self):
        return hash(self.x)

    def __eq__(self, other: 'Float3') -> bool:
        if self.x != other.x: return False
        if self.y != other.y: return False
        if self.z != other.z: return False
        return True

    def __repr__(self) -> str:
        return f'({self.x}, {self.y}, {self.z})'

    def __sub__(self, rhs):
        return Float3(self.x - rhs.x, self.y - rhs.y, self.z - rhs.z)

    def __add__(self, rhs):
        return Float3(self.x + rhs.x, self.y + rhs.y, self.z + rhs.z)


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

    def __repr__(self) -> str:
        return f'({self.x}, {self.y}, {self.z}, {self.w})'

    def __eq__(self, other: 'Float4') -> bool:
        if self.x != other.x: return False
        if self.y != other.y: return False
        if self.z != other.z: return False
        if self.w != other.w: return False
        return True

    def __mul__(self, factor: float) -> 'Float4':
        return Float4(self.x * factor, self.y * factor, self.z * factor,
                      self.w * factor)


class Mat4(ctypes.Structure):
    _pack_ = 1
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
    def identity() -> 'Mat4':
        return Mat4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
                    0.0, 0.0, 0.0, 1.0)

    @staticmethod
    def translation(x: float, y: float, z: float) -> 'Mat4':
        return Mat4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
                    x, y, z, 1.0)


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
    def create(vertex_count: int, has_bone_weight: bool) -> 'PlanarBuffer':
        pos = (Float3 * vertex_count)()
        nom = (Float3 * vertex_count)()
        uv = (Float2 * vertex_count)()
        if has_bone_weight:
            joints = (UShort4 * vertex_count)()
            weights = (Float4 * vertex_count)()
        else:
            joints = None
            weights = None
        return PlanarBuffer(pos, nom, uv, joints, weights)  # type: ignore


def get_min_max2(list: Iterable[Float2]):
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


class BoneWeight(ctypes.LittleEndianStructure):
    _fields_ = [
        ("joints", UShort4),
        ("weights", Float4),
    ]

    def push(self, i: int, w: float):
        if self.weights.x == 0:
            self.joints.x = i
            self.weights.x = w
        elif self.weights.y == 0:
            self.joints.y = i
            self.weights.y = w
        elif self.weights.z == 0:
            self.joints.z = i
            self.weights.z = w
        elif self.weights.w == 0:
            self.joints.w = i
            self.weights.w = w
        else:
            raise NotImplementedError('over 4')

    def to_joints_with_weights(
            self,
            group_index_to_joint_index: Dict[int,
                                             int]) -> Tuple[UShort4, Float4]:
        '''
        ついでに正規化する
        '''
        total_weights = (self.weights.x + self.weights.y + self.weights.z +
                         self.weights.w)
        factor = 1 / total_weights

        joints = UShort4(
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
