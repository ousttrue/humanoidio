'''
custom RNA property definitions
'''

import bpy
from bpy import types

from pyimpex import CLASSES
from .. import formats
from .expression import PYIMPEX_Expression, PYIMPEX_UL_ExpressionTemplate, PYIMPEX_ExpressionPanel
from .humanoid import PYIMPEX_HumanoidBonePanel
from .meta import PYIMPEX_Meta

CLASSES = [
    PYIMPEX_Expression, PYIMPEX_UL_ExpressionTemplate, PYIMPEX_ExpressionPanel,
    PYIMPEX_HumanoidBonePanel, PYIMPEX_Meta
]


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

    #
    # Object.meta
    #
    bpy.types.Object.pyimpex_meta = bpy.props.PointerProperty(
        type=PYIMPEX_Meta)

    #
    # Object.expressions
    #
    bpy.types.Object.pyimpex_expressions = bpy.props.CollectionProperty(  # type: ignore
        type=PYIMPEX_Expression)
    bpy.types.Object.pyimpex_expressions_active = bpy.props.IntProperty(  # type: ignore
    )

    #
    # PoseBone.humanoid_bone
    #
    items = (
        (bone.name, bone.name, bone.name)  # (識別子, UI表示名, 説明文)
        for bone in formats.HumanoidBones)
    bpy.types.PoseBone.pyimpex_humanoid_bone = bpy.props.EnumProperty(
        items=items)


def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
