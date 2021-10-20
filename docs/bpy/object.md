# object

```py
import bpy

# bpy.context.object is readonly
data = bpy.context.object.data
if isinstance(data, bpy.types.Mesh):
	print('is mesh')
```

## active

```py
# edit mode
bpy.context.view_layer.objects.active = obj
print(bpy.context.object.mode)

bpy.ops.object.mode_set(mode='EDIT')
```
