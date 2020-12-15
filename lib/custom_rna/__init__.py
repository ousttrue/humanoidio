'''
custom RNA property definitions
'''

import bpy
from bpy import types

from pyimpex import CLASSES
from .. import formats
from . import expression, humanoid, meta, view_bookmark


def reload():
    # print(f'reload {__file__}')
    from . import expression, humanoid, meta, view_bookmark
    import importlib
    for m in [expression, humanoid, meta, view_bookmark]:
        importlib.reload(m)


def register():
    expression.register()
    humanoid.register()
    meta.register()
    view_bookmark.register()


def unregister():
    view_bookmark.unregister()
    meta.unregister()
    humanoid.unregister()
    expression.unregister()
