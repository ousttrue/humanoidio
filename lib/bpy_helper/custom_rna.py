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


class PYIMPEX_Expression(bpy.types.PropertyGroup):
    preset: bpy.props.EnumProperty(name="Expression preset",
                                   description="VRM Expression preset",
                                   items=presets)
    name: bpy.props.StringProperty(name="Preset", default="Unknown")


class PYIMPEX_UL_ExpressionTemplate(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class PYIMPEX_ExpressionPanel(bpy.types.Panel):
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
        layout.template_list(
            "PYIMPEX_UL_ExpressionTemplate",
            "",
            # list
            obj,
            "pyimpex_expressions",
            # index
            obj,
            "pyimpex_expressions_active")


def register():
    bpy.utils.register_class(PYIMPEX_Expression)
    bpy.utils.register_class(PYIMPEX_UL_ExpressionTemplate)

    bpy.types.Object.pyimpex_expressions = bpy.props.CollectionProperty(  # type: ignore
        type=PYIMPEX_Expression)
    bpy.types.Object.pyimpex_expressions_active = bpy.props.IntProperty(  # type: ignore
    )

    bpy.utils.register_class(PYIMPEX_ExpressionPanel)
