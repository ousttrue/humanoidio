# Mesh

## empty mesh

```py
import bpy
# Create an empty mesh and the object.
mesh = bpy.data.meshes.new('MeshData')
basic_cube = bpy.data.objects.new("MeshObj", mesh)
# Add the object into the scene.
bpy.context.scene.collection.objects.link(basic_cube)
# Activate
bpy.context.view_layer.objects.active = basic_cube
basic_cube.select_set(True)
```
