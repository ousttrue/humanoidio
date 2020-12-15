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
    weight: bpy.props.FloatProperty(name="Weight", default=0, min=0, max=1)


class PYIMPEX_UL_ExpressionTemplate(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "preset", text="", emboss=False, icon_value=icon)
            layout.prop(item, "name", text="", emboss=False)
            layout.prop(item, "weight", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class PYIMPEX_ExpressionPanel(bpy.types.Panel):
    '''
    表情操作パネル
    '''
    bl_idname = "OBJECT_PT_pyimex_expression"
    bl_label = "VRM Expressions"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if not isinstance(context.object.data, bpy.types.Armature):
            return False

        return True

    def draw_header(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.label(text="pyimpex Expressions")

    def draw(self, context):
        layout = self.layout
        obj = context.object

        row = layout.row()
        row.template_list(
            "PYIMPEX_UL_ExpressionTemplate",
            "Expresssions",
            # list
            obj,
            "pyimpex_expressions",
            # index
            obj,
            "pyimpex_expressions_active")

        row = layout.row()
