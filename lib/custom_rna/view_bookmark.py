'''
3D view port のカメラ位置を bookmark する。
GreacePencil と使う予定
'''
import bpy

bpy.props.FloatVectorProperty


class PYIMPEX_ViewBookmark(bpy.types.PropertyGroup):
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


class PYIMPEX_UL_ViewBookmarkTemplate(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        layout.alignment = 'CENTER'
        layout.label(text="view")


class PYIMPEX_OT_RegisterViewBookmark(bpy.types.Operator):
    '''
    視点を登録する
    '''
    bl_idname = "pyimpex.register_viewbookmark"
    bl_label = "bookmark view"
    bl_options = {'REGISTER', 'UNDO'}

    #--- execute ---#
    def register(self, scene: bpy.types.Scene, space: bpy.types.RegionView3D):
        bookmark: PYIMPEX_ViewBookmark = scene.pyimpex_viewbookmarks.add()
        bookmark.view_matrix = [x for row in space.view_matrix for x in row]

    def execute(self, context: bpy.types.Context):
        for sp in context.area.spaces:
            if isinstance(sp, bpy.types.SpaceView3D):
                self.register(context.scene, sp.region_3d)

        self.report({'INFO'}, f'op: register view bookmark')

        return {'FINISHED'}


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
        row.template_list(
            "PYIMPEX_UL_ViewBookmarkTemplate",
            "View Bookmarks",
            # list
            context.scene,
            "pyimpex_viewbookmarks",
            # index
            context.scene,
            "pyimpex_viewbookmarks_active")

        layout.operator(PYIMPEX_OT_RegisterViewBookmark.bl_idname)
