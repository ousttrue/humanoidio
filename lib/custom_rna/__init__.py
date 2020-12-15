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
from .view_bookmark import PYIMPEX_PT_ViewBookmark, PYIMPEX_OT_RegisterViewBookmark, PYIMPEX_ViewBookmark, PYIMPEX_UL_ViewBookmarkTemplate

CLASSES = [
    PYIMPEX_Expression,
    PYIMPEX_UL_ExpressionTemplate,
    PYIMPEX_ExpressionPanel,
    #
    PYIMPEX_HumanoidBonePanel,
    #
    PYIMPEX_Meta,
    #
    PYIMPEX_ViewBookmark,
    PYIMPEX_UL_ViewBookmarkTemplate,
    PYIMPEX_PT_ViewBookmark,
    PYIMPEX_OT_RegisterViewBookmark,
]


def reload():
    # print(f'reload {__file__}')
    from . import expression, humanoid, meta, view_bookmark
    import importlib
    for m in [expression, humanoid, meta, view_bookmark]:
        importlib.reload(m)


def register():
    try:
        for c in CLASSES:
            bpy.utils.register_class(c)
    except:
        pass

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

    #
    # Scene.bookmakviews
    #
    bpy.types.Scene.pyimpex_viewbookmarks = bpy.props.CollectionProperty(  # type: ignore
        type=PYIMPEX_ViewBookmark)
    bpy.types.Scene.pyimpex_viewbookmarks_active = bpy.props.IntProperty(  # type: ignore
    )


def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
