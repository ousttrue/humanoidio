'''
* https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo#Script_Meta_Info
* https://github.com/dfelinto/blender/blob/master/release/scripts/modules/addon_utils.py
'''
bl_info = {
    "name": "pyimpex",
    "author": "ousttrue",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "scene import and export",
    "doc_url": "https://github.com/ousttrue/pyimpex",
    "category": "Import-Export",
    "support": "TESTING",
    "warning": "This addon is still in development.",
}

from logging import getLogger
logger = getLogger(__name__)
import pathlib


def reload():
    print('reload')
    import importlib

    from .lib import formats
    importlib.reload(formats)

    from .lib import pyscene
    pyscene.reload()

    from .lib import bpy_helper
    bpy_helper.reload()

    from .lib import custom_rna
    custom_rna.reload()


if "bpy" in locals():
    reload()

#
import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (ImportHelper, ExportHelper)


class PyImpexImporter(bpy.types.Operator, ImportHelper):
    """
    Import scene
    """
    bl_idname = 'pyimpex.importer'
    bl_label = 'Scene Importer'
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob: StringProperty(
        default='*.vrm;*.glb;*.gltf',
        options={'HIDDEN'},
    )

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')

        #
        # read data
        #
        path = pathlib.Path(self.filepath).absolute()  # type: ignore

        from .lib import formats
        data = formats.parse_gltf(path)

        from .lib import pyscene
        index_map = pyscene.load(data)

        #
        # import to blender
        #
        collection = bpy.data.collections.new(name=path.name)
        context.scene.collection.children.link(collection)

        from .lib import bpy_helper
        bpy_helper.importer.load(collection, index_map)

        # color management
        bpy.context.scene.view_settings.view_transform = 'Standard'

        return {'FINISHED'}


class PyImpexExporter(bpy.types.Operator, ExportHelper):
    """
    Export scene
    """
    bl_idname = 'pyimpex.exporter'
    bl_label = 'Scene Exporter'
    bl_options = {'PRESET'}

    filename_ext = '.glb'
    filter_glob: StringProperty(
        default='*.glb',
        options={'HIDDEN'},
    )

    check_extension = True

    def execute(self, context: bpy.types.Context):
        logger.debug('#### start ####')

        from .lib import bpy_helper
        export_map = bpy_helper.exporter.scan()
        data = bpy_helper.exporter.to_gltf(export_map)
        d = data.gltf.to_dict()

        from .lib import formats
        text = formats.to_json(d)
        json_bytes = text.encode('utf-8')

        from .lib.formats.glb import Glb
        pathlib.Path(self.filepath).parent.mkdir(exist_ok=True, parents=True)
        with open(self.filepath, 'wb') as w:  # type: ignore
            Glb(json_bytes, data.bin).write_to(w)

        return {'FINISHED'}


class PyImpexSimetrizeVertexGroup(bpy.types.Operator):
    """ Create empty opotunity vertex group that name ends_with `_L`, `.L`
    """
    bl_idname = "pyimpex.symetrize_vertexgroup"
    bl_label = "Symetrize vertex group"

    def execute(self, context: bpy.types.Context):
        o = context.active_object
        if o and isinstance(o.data, bpy.types.Mesh):
            vg_names = [vg.name for vg in o.vertex_groups]

            def opposite(name: str):
                if name.endswith('.L'):
                    return name[0:-2] + '.R'
                if name.endswith('.R'):
                    return name[0:-2] + '.L'
                if name.endswith('_L'):
                    return name[0:-2] + '_R'
                if name.endswith('_R'):
                    return name[0:-2] + '_L'

            for name in vg_names:
                if not name:
                    continue
                new_name = opposite(name)
                if not new_name:
                    continue
                other_group = o.vertex_groups.get(new_name)
                if not other_group:
                    print(f'create vertex_group: {new_name}')
                    self.report({'INFO'}, f'create vertex_group: {new_name}')
                    o.vertex_groups.new(name=new_name)

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class PyImpexDeselectInAnyVertexGroup(bpy.types.Operator):
    """ Deselect vertices belong to any vertex group
    """
    bl_idname = "pyimpex.deselect_in_any_vertexgroup"
    bl_label = "Deselect vertex in any vertexgroup"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.object
        if not isinstance(obj, bpy.types.Object):
            return False
        if not isinstance(obj.data, bpy.types.Mesh):
            return False
        if obj.mode != 'EDIT':
            return False
        return True

    def execute(self, context: bpy.types.Context):
        obj = context.object
        if not isinstance(obj, bpy.types.Object):
            return {'CANCELLED'}
        mesh = obj.data
        if not isinstance(mesh, bpy.types.Mesh):
            return {'CANCELLED'}

        des = []
        for i, v in enumerate(mesh.vertices):
            for g in v.groups:
                if g.weight > 0:
                    des.append(i)
                    break

        import bmesh
        bm = bmesh.from_edit_mesh(mesh)
        bm.select_mode = {'VERT'}
        for i in des:
            bm.verts[i].select = False
        bm.select_flush_mode()
        mesh.update()

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class PyImpexGuessHumanoidSkeleton(bpy.types.Operator):
    """ Guess humanoid skeleton
    """
    bl_idname = "pyimpex.guess_humanoid"
    bl_label = "Guess humanoid bone assignment"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.object
        if not isinstance(obj, bpy.types.Object):
            return False
        if not isinstance(obj.data, bpy.types.Armature):
            return False
        if obj.mode != 'POSE':
            return False
        return True

    def execute(self, context: bpy.types.Context):
        obj = context.object
        if not isinstance(obj, bpy.types.Object):
            return {'CANCELLED'}
        armature = obj.data
        if not isinstance(armature, bpy.types.Armature):
            return {'CANCELLED'}

        from .lib import formats
        used = {}
        for bone in obj.pose.bones:
            src = formats.HumanoidBones[bone.pyimpex_humanoid_bone]
            if src != formats.HumanoidBones.unknown:
                used[src] = True

        name_to_bone = {
            'hips': formats.HumanoidBones.hips,
            'spine': formats.HumanoidBones.spine,
            'chest': formats.HumanoidBones.chest,
            'neck': formats.HumanoidBones.neck,
            'head': formats.HumanoidBones.head,
            # LR
            'shoulder_L': formats.HumanoidBones.leftShoulder,
            'upperArm_L': formats.HumanoidBones.leftUpperArm,
            'lowerArm_L': formats.HumanoidBones.leftLowerArm,
            'hand_L': formats.HumanoidBones.leftHand,
            'upperLeg_L': formats.HumanoidBones.leftUpperLeg,
            'lowerLeg_L': formats.HumanoidBones.leftLowerLeg,
            'foot_L': formats.HumanoidBones.leftFoot,
            'toes_L': formats.HumanoidBones.leftToes,
            'shoulder_R': formats.HumanoidBones.rightShoulder,
            'upperArm_R': formats.HumanoidBones.rightUpperArm,
            'lowerArm_R': formats.HumanoidBones.rightLowerArm,
            'hand_R': formats.HumanoidBones.rightHand,
            'upperLeg_R': formats.HumanoidBones.rightUpperLeg,
            'lowerLeg_R': formats.HumanoidBones.rightLowerLeg,
            'foot_R': formats.HumanoidBones.rightFoot,
            'toes_R': formats.HumanoidBones.rightToes,
            # fingers L
            'thumb0_L': formats.HumanoidBones.leftThumbProximal,
            'thumb1_L': formats.HumanoidBones.leftThumbIntermediate,
            'thumb2_L': formats.HumanoidBones.leftThumbDistal,
            'index0_L': formats.HumanoidBones.leftIndexProximal,
            'index1_L': formats.HumanoidBones.leftIndexIntermediate,
            'index2_L': formats.HumanoidBones.leftIndexDistal,
            'middle0_L': formats.HumanoidBones.leftMiddleProximal,
            'middle1_L': formats.HumanoidBones.leftMiddleIntermediate,
            'middle2_L': formats.HumanoidBones.leftMiddleDistal,
            'ring0_L': formats.HumanoidBones.leftRingProximal,
            'ring1_L': formats.HumanoidBones.leftRingIntermediate,
            'ring2_L': formats.HumanoidBones.leftRingDistal,
            'little0_L': formats.HumanoidBones.leftLittleProximal,
            'little1_L': formats.HumanoidBones.leftLittleIntermediate,
            'little2_L': formats.HumanoidBones.leftLittleDistal,
            # fingers R
            'thumb0_R': formats.HumanoidBones.rightThumbProximal,
            'thumb1_R': formats.HumanoidBones.rightThumbIntermediate,
            'thumb2_R': formats.HumanoidBones.rightThumbDistal,
            'index0_R': formats.HumanoidBones.rightIndexProximal,
            'index1_R': formats.HumanoidBones.rightIndexIntermediate,
            'index2_R': formats.HumanoidBones.rightIndexDistal,
            'middle0_R': formats.HumanoidBones.rightMiddleProximal,
            'middle1_R': formats.HumanoidBones.rightMiddleIntermediate,
            'middle2_R': formats.HumanoidBones.rightMiddleDistal,
            'ring0_R': formats.HumanoidBones.rightRingProximal,
            'ring1_R': formats.HumanoidBones.rightRingIntermediate,
            'ring2_R': formats.HumanoidBones.rightRingDistal,
            'little0_R': formats.HumanoidBones.rightLittleProximal,
            'little1_R': formats.HumanoidBones.rightLittleIntermediate,
            'little2_R': formats.HumanoidBones.rightLittleDistal,
        }

        def guess_bone(name: str) -> formats.HumanoidBones:
            print(f'guess: {name}')
            return name_to_bone.get(name, formats.HumanoidBones.unknown)

        for bone in obj.pose.bones:
            src = formats.HumanoidBones[bone.pyimpex_humanoid_bone]
            if src == formats.HumanoidBones.unknown:
                humanoid_bone = guess_bone(bone.name)
                if humanoid_bone not in used:
                    print(f'{bone} => {humanoid_bone}')
                    bone.pyimpex_humanoid_bone = humanoid_bone.name

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


CLASSES = [
    PyImpexImporter, PyImpexExporter, PyImpexSimetrizeVertexGroup,
    PyImpexDeselectInAnyVertexGroup, PyImpexGuessHumanoidSkeleton
]


def menu_func_import(self, context):
    self.layout.operator(PyImpexImporter.bl_idname,
                         text=f"pyimpex (.gltf;.glb;.vrm)")


def menu_func_export(self, context):
    self.layout.operator(PyImpexExporter.bl_idname, text=f"pyimpex (.glb)")


def register():
    from .lib import custom_rna
    import importlib
    importlib.reload(custom_rna)
    custom_rna.register()

    # operators
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)  # type: ignore
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)  # type: ignore


def unregister():
    # Note: when unregister, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for c in CLASSES:
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)  # type: ignore
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)  # type: ignore

    #
    from .lib import custom_rna
    custom_rna.unregister()


if __name__ == "__main__":
    register()
