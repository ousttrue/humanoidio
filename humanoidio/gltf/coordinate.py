from typing import NamedTuple, Iterable, Any, Generator
from enum import IntEnum, auto


class Coodinate(IntEnum):
    # [glTF, VRM1]
    #    Y  Z
    #    | /
    # X--+
    RH_XYZ_left_up_forward = auto()
    GLTF = RH_XYZ_left_up_forward
    VRM1 = RH_XYZ_left_up_forward
    # [VRM0]
    #    Y
    #    |
    #    +--X
    #   /
    # Z
    RH_XYZ_right_up_backward = auto()
    VRM0 = RH_XYZ_right_up_backward
    # [blender]
    # Z  Y
    # | /
    # +--X
    RH_XYZ_right_forward_up = auto()
    BLENDER = RH_XYZ_right_forward_up
    # Blender でこっち向きにモデルをロードする
    RH_XYZ_left_backword_up = auto()
    BLENDER_ROTATE = RH_XYZ_left_backword_up
    # [Unity]
    # Y  Z
    # | /
    # +--X
    LH_XYZ_right_up_forward = auto()
    UNITY = LH_XYZ_right_up_forward


def yup2zup_turn(iterable) -> Generator[Any, None, None]:
    def g():
        it = iter(iterable)
        while True:
            try:
                _0 = next(it)
                _1 = next(it)
                _2 = next(it)
                yield (-_0, _2, _1)
            except StopIteration:
                break

    return g


def yup2zup(iterable) -> Generator[Any, None, None]:
    def g():
        it = iter(iterable)
        while True:
            try:
                _0 = next(it)
                _1 = next(it)
                _2 = next(it)
                yield (_0, -_2, _1)
            except StopIteration:
                break

    return g


class Conversion(NamedTuple):
    src: Coodinate
    dst: Coodinate

    def generator(self, span: Iterable[Any]) -> Generator[Any, None, None]:
        if self.dst == Coodinate.BLENDER:
            # [blender]
            # Z  Y
            # | /
            # +--X
            if self.src == Coodinate.GLTF:
                # [glTF, VRM1]
                #    Y  Z
                #    | /
                # X--+
                return yup2zup_turn(span)
            elif self.src == Coodinate.VRM0:
                # [VRM0]
                #    Y
                #    |
                #    +--X
                #   /
                # Z
                return yup2zup(span)
            else:
                raise NotImplementedError()
        elif self.dst == Coodinate.BLENDER_ROTATE:
            # [blender]
            #    z
            #    |
            # X--+
            #   /
            # y
            if self.src == Coodinate.GLTF:
                # [glTF, VRM1]
                #    Y  Z
                #    | /
                # X--+
                return yup2zup(span)
            elif self.src == Coodinate.VRM0:
                # [VRM0]
                #    Y
                #    |
                #    +--X
                #   /
                # Z
                return yup2zup_turn(span)
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()
