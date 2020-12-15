import bpy


class PYIMPEX_Meta(bpy.types.PropertyGroup):
    title: bpy.props.StringProperty(name="title", description="VRM Meta title")
    author: bpy.props.StringProperty(name="author",
                                     description="VRM Meta author")
    version: bpy.props.StringProperty(name="version",
                                      description="VRM Meta version")


CLASSES = [PYIMPEX_Meta]


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

def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
