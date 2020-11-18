'''
custom RNA property definitions
'''

import bpy

presets = (
    ('unknown', 'unknown', ''),
    ('neutral', 'neutral', ''),
    ('a', 'a', ''),
    ('i', 'i', ''),
    ('u', 'u', ''),
    ('e', 'e', ''),
    ('o', 'o', ''),
    ('blink', 'blink', ''),
    ('joy', 'joy', ''),
    ('angry', 'angry', ''),
    ('sorrow', 'sorrow', ''),
    ('fun', 'fun', ''),
    ('lookup', 'lookup', ''),
    ('lookdown', 'lookdown', ''),
    ('lookleft', 'lookleft', ''),
    ('lookright', 'lookright', ''),
    ('blink_l', 'blink_l', ''),
    ('blink_r', 'blink_r', ''),
)


class Expression(bpy.types.PropertyGroup):
    preset: bpy.props.EnumProperty(name="Expression preset",
                                   description="VRM Expression preset",
                                   items=presets)
    name: bpy.props.StringProperty(name="Preset", default="Unknown")


class MESH_UL_expressions(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        print(item)
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class PyImpexExpressionPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_pyimex_expression"
    bl_label = "VRM Expressions"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        return True

    def draw_header(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.label(text="pyimpex Expressions")

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # template_list now takes two new args.
        # The first one is the identifier of the registered UIList to use (if you want only the default list,
        # with no custom draw code, use "UI_UL_list").
        layout.template_list("MESH_UL_expressions", "", obj,
                             "pyimpex_expressions", obj.pyimpex_expressions,
                             "active_index")


def register():
    bpy.utils.register_class(Expression)
    bpy.types.Object.pyimpex_expressions = bpy.props.CollectionProperty(  # type: ignore
        type=Expression)
    bpy.utils.register_class(PyImpexExpressionPanel)
