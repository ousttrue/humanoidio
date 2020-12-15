import bpy
from .. import formats


class PYIMPEX_HumanoidBonePanel(bpy.types.Panel):
    '''
    context.active_pose_bone に対して Humanoid bone 選択パネルを表示する
    '''
    bl_idname = "OBJECT_PT_pyimex_humanoidbone"
    bl_label = "VRM HumanoidBone"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if not isinstance(context.object.data, bpy.types.Armature):
            return False

        return True

    def draw_header(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.label(text="pyimpex Humanoid")

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row()
        if context.active_pose_bone:
            row.prop(context.active_pose_bone,
                     'pyimpex_humanoid_bone',
                     text='humanoid bone')


CLASSES = [
    PYIMPEX_HumanoidBonePanel,
]


def register():
    try:
        for c in CLASSES:
            bpy.utils.register_class(c)
    except:
        pass

    #
    # PoseBone.humanoid_bone
    #
    items = (
        (bone.name, bone.name, bone.name)  # (識別子, UI表示名, 説明文)
        for bone in formats.HumanoidBones)
    bpy.types.PoseBone.pyimpex_humanoid_bone = bpy.props.EnumProperty(
        items=items)


def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
