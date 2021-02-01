'''
3D view port のカメラ位置を bookmark する。
GreacePencil と使う予定
'''
from typing import Optional
import bpy

bpy.props.FloatVectorProperty


class PYIMPEX_ViewBookmark(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    view_matrix: bpy.props.FloatVectorProperty(
        name="view_matrix",
        default=(
            1,
            0,
            0,
            0,  # 
            0,
            1,
            0,
            0,  #
            0,
            0,
            1,
            0,  #
            0,
            0,
            0,
            1),
        subtype='MATRIX',
        size=16,
        description="view matrix",
    )


def get_region() -> Optional[bpy.types.RegionView3D]:
    for sp in bpy.context.area.spaces:
        if isinstance(sp, bpy.types.SpaceView3D):
            return sp.region_3d


class PYIMPEX_ViewBookmarks(bpy.types.PropertyGroup):
    active: bpy.props.IntProperty()
    list: bpy.props.CollectionProperty(type=PYIMPEX_ViewBookmark)

    def update_item(self, item: PYIMPEX_ViewBookmark,
                    region: bpy.types.RegionView3D):
        m = [x for row in region.view_matrix for x in row]
        x = m[3]
        y = m[7]
        z = m[11]
        item.name = f'[{x:.1f}, {y:.1f}, {z:.1f}]'
        item.view_matrix = m

    def add(self):
        item: PYIMPEX_ViewBookmark = self.list.add()
        self.active = len(self.list) - 1
        item.name = 'no view'
        region = get_region()
        if region:
            self.update_item(item, region)

    def remove(self):
        if len(self.list):
            self.list.remove(self.active)
            if len(self.list) - 1 < self.active:
                self.active = len(self.list) - 1
                if self.active < 0:
                    self.active = 0

    def move(self, index1, index2):
        if len(self.list) < 2:
            return
        if 0 <= index1 < len(self.list):
            if 0 <= index2 < len(self.list):
                self.list.move(index1, index2)
                self.active = index2

    def clear(self):
        self.list.clear()

    def get(self, index: int) -> Optional[PYIMPEX_ViewBookmark]:
        if index >= 0 and index < len(self.list):
            return self.list[index]


class PYIMPEX_OT_AddViewBookmark(bpy.types.Operator):
    bl_idname = "pyimpex.add_viewbookmark"
    bl_label = "Add Item"

    def execute(self, context):
        context.scene.pyimpex_viewbookmarks.add()
        return {'FINISHED'}


class PYIMPEX_OT_RemoveViewBookmark(bpy.types.Operator):
    bl_idname = "pyimpex.remove_viewbookmark"
    bl_label = "Remove Item"

    def execute(self, context):
        context.scene.pyimpex_viewbookmarks.remove()
        return {'FINISHED'}


class PYIMPEX_OT_MoveViewBookmark(bpy.types.Operator):
    bl_idname = "pyimpex.move_viewbookmark"
    bl_label = "Move Item"

    type: bpy.props.StringProperty(default='UP')

    def execute(self, context):
        ui_list = context.scene.pyimpex_viewbookmarks
        if self.type == 'UP':
            ui_list.move(ui_list.active_index, ui_list.active_index - 1)
        elif self.type == 'DOWN':
            ui_list.move(ui_list.active_index, ui_list.active_index + 1)
        return {'FINISHED'}


class PYIMPEX_OT_ClearViewBookmark(bpy.types.Operator):
    bl_idname = "pyimpex.clear_viewbookmark"
    bl_label = "Clear Item"

    def execute(self, context):
        context.scene.pyimpex_viewbookmarks.clear()
        return {'FINISHED'}


class PYIMPEX_OT_ApplyViewBookmark(bpy.types.Operator):
    bl_idname = "pyimpex.apply_viewbookmark"
    bl_label = "Apply Item"

    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        index = self.index
        if index == -1:
            index = context.scene.pyimpex_viewbookmarks.active

        item = context.scene.pyimpex_viewbookmarks.get(index)
        if item:
            region = get_region()
            if region:
                m = [x for x in item.view_matrix]
                region.view_matrix = m

        return {'FINISHED'}


class PYIMPEX_UL_ViewBookmarkTemplate(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # layout.prop(item, "preset", text="", emboss=False, icon_value=icon)
            layout.prop(item, "name", text="", emboss=False)
            layout.operator("pyimpex.apply_viewbookmark",
                            icon="VIEW_CAMERA",
                            text="").index = index
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class PYIMPEX_PT_ViewBookmark(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    # rightside
    bl_region_type = 'UI'
    # tab
    bl_category = "View"
    # fold
    bl_label = "Bookmarks"

    #--- draw ---#
    def draw(self, context: bpy.types.Context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.template_list(
            "PYIMPEX_UL_ViewBookmarkTemplate",
            "View Bookmarks",
            # list
            context.scene.pyimpex_viewbookmarks,
            "list",
            # index
            context.scene.pyimpex_viewbookmarks,
            "active")

        col = row.column(align=True)
        col.operator("pyimpex.add_viewbookmark", icon='ADD', text="")
        col.operator("pyimpex.remove_viewbookmark", icon='REMOVE', text="")
        col.operator("pyimpex.move_viewbookmark", icon='TRIA_UP',
                     text="").type = 'UP'
        col.operator("pyimpex.move_viewbookmark", icon='TRIA_DOWN',
                     text="").type = 'DOWN'
        layout.operator("pyimpex.clear_viewbookmark", text="All Clear")


CLASSES = [
    PYIMPEX_ViewBookmark,
    PYIMPEX_ViewBookmarks,
    PYIMPEX_OT_AddViewBookmark,
    PYIMPEX_OT_RemoveViewBookmark,
    PYIMPEX_OT_MoveViewBookmark,
    PYIMPEX_OT_ClearViewBookmark,
    PYIMPEX_OT_ApplyViewBookmark,
    PYIMPEX_UL_ViewBookmarkTemplate,
    PYIMPEX_PT_ViewBookmark,
]


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

    #
    # Scene.bookmakviews
    #
    bpy.types.Scene.pyimpex_viewbookmarks = bpy.props.PointerProperty(
        type=PYIMPEX_ViewBookmarks)


def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
