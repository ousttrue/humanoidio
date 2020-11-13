from typing import Optional
from enum import Enum
from .. import formats
from .index_map import IndexMap


class VrmExpressionPreset(Enum):
    unknown = "unknown"
    neutral = "neutral"
    a = "a"
    i = "i"
    u = "u"
    e = "e"
    o = "o"
    blink = "blink"
    joy = "joy"
    angry = "angry"
    sorrow = "sorrow"
    fun = "fun"
    lookup = "lookup"
    lookdown = "lookdown"
    lookleft = "lookleft"
    lookright = "lookright"
    blink_l = "blink_l"
    blink_r = "blink_r"


class VrmExpression:
    def __init__(self, preset: VrmExpressionPreset,
                 name: Optional[str]) -> None:
        self.preset = preset
        self.name = name

    def __str__(self) -> str:
        if self.preset == VrmExpressionPreset.unknown:
            return f'custom: {self.name}'
        else:
            return f'{self.preset}'

    def __repr__(self) -> str:
        if self.preset == VrmExpressionPreset.unknown:
            return f'VrmExpression({self.preset}, "{self.name}")'
        else:
            return f'VrmExpression({self.preset})'


class Vrm:
    def __init__(self) -> None:
        self.expressions = []


def load_vrm(index_map: IndexMap, gltf: formats.gltf.glTF) -> Optional[Vrm]:
    if not gltf.extensions:
        return None
    if not gltf.extensions.VRM:
        return None

    vrm = Vrm()
    for blendshape in gltf.extensions.VRM.blendShapeMaster.blendShapeGroups:
        if not isinstance(blendshape.name, str):
            raise Exception()
        if not blendshape.presetName:
            raise Exception()
        expression = VrmExpression(VrmExpressionPreset(blendshape.presetName),
                                   blendshape.name)
        vrm.expressions.append(expression)
    return vrm
