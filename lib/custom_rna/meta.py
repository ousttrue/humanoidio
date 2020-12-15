import bpy


class PYIMPEX_Meta(bpy.types.PropertyGroup):
    title: bpy.props.StringProperty(name="title", description="VRM Meta title")
    author: bpy.props.StringProperty(name="author",
                                     description="VRM Meta author")
    version: bpy.props.StringProperty(name="version",
                                      description="VRM Meta version")
