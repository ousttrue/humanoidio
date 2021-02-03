'''
custom RNA property definitions
'''

from pyimpex import CLASSES
from . import expression, humanoid, meta, view_bookmark, material


def reload():
    # print(f'reload {__file__}')
    from . import expression, humanoid, meta, view_bookmark, material
    import importlib
    for m in [expression, humanoid, meta, view_bookmark, material]:
        importlib.reload(m)


def register():
    expression.register()
    humanoid.register()
    meta.register()
    view_bookmark.register()
    material.register()


def unregister():
    material.unregister()
    view_bookmark.unregister()
    meta.unregister()
    humanoid.unregister()
    expression.unregister()
