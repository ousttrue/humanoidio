import bpy
from bpy.props import StringProperty


class PYIMPEX_CreateVrmMaterial(bpy.types.Operator):
    """ Create default node graph for vrm
    """
    bl_idname = "pyimpex.create_vrm_material"
    bl_label = "Create VRM node graph to the active material"

    material_type: StringProperty(default='unlit')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.object
        if not isinstance(obj, bpy.types.Object):
            return False
        if not isinstance(obj.data, bpy.types.Mesh):
            return False
        if not obj.active_material:
            return False
        return True

    def execute(self, context: bpy.types.Context):
        obj = context.object
        if not isinstance(obj, bpy.types.Object):
            return {'CANCELLED'}
        mesh = obj.data
        if not isinstance(mesh, bpy.types.Mesh):
            return {'CANCELLED'}
        material = obj.active_material
        if not isinstance(material, bpy.types.Material):
            return {'CANCELLED'}

        if self.material_type == 'unlit':
            material.use_nodes = True
            material.node_tree.nodes.clear()
            from .. import pyscene
            from ..bpy_helper.materials import unlit_material
            unlit_material.build(material,
                                 pyscene.UnlitMaterial(material.name), None)
        elif self.material_type == 'mtoon':
            material.use_nodes = True
            material.node_tree.nodes.clear()
            from .. import pyscene
            from ..bpy_helper.materials import mtoon_material
            mtoon_material.build(material,
                                 pyscene.MToonMaterial(material.name), None)
        elif self.material_type == 'pbr':
            material.use_nodes = True
            material.node_tree.nodes.clear()
            from .. import pyscene
            from ..bpy_helper.materials import pbr_material
            pbr_material.build(material, pyscene.PBRMaterial(material.name),
                               None)
        else:
            print(f'unknown: {self.material_type}')

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class PYIMPEX_MaterialPanel(bpy.types.Panel):
    '''
    context.object に対して Material 生成ボタン
    '''
    bl_idname = "OBJECT_PT_pyimex_material"
    bl_label = "VRM Material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        if not isinstance(context.object, bpy.types.Object):
            return False
        if not isinstance(context.object.data, bpy.types.Mesh):
            return False

        return True

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row()

        material = context.active_object.active_material
        if isinstance(material, bpy.types.Material):
            # row.label(text=f'vrm material: {material.name}', icon='INFO')
            unlit = row.operator(PYIMPEX_CreateVrmMaterial.bl_idname,
                                 text='unlit')
            unlit.material_type = 'unlit'

            mtoon = row.operator(PYIMPEX_CreateVrmMaterial.bl_idname,
                                 text='mtoon')
            mtoon.material_type = 'mtoon'

            pbr = row.operator(PYIMPEX_CreateVrmMaterial.bl_idname, text='pbr')
            pbr.material_type = 'pbr'
        else:
            row.label(text=f'no active material', icon='INFO')


CLASSES = [
    PYIMPEX_CreateVrmMaterial,
    PYIMPEX_MaterialPanel,
]


def register():
    try:
        for c in CLASSES:
            bpy.utils.register_class(c)
    except:
        pass


def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
