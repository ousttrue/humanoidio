# bpy.context

<https://docs.blender.org/api/current/bpy.context.html>

> Note that all context values are readonly, but may be modified through the data API or by running operators

| prop             |  |
|------------------|--|
| object           |  |
| active_object    |  |
| selected_objects |  |
| mode             |  |


## Contextオーバーライド

<https://docs.blender.org/api/blender2.8/bpy.ops.html#overriding-context>

```py
# remove all objects in scene rather than the selected ones
import bpy
override = bpy.context.copy()
override['selected_objects'] = list(bpy.context.scene.objects)
bpy.ops.object.delete(override)
```
