# scene and collection

* <https://code.blender.org/2017/09/view-layers-and-collections/>
* <https://code.blender.org/2018/05/collections-and-groups/>

## active scene

`bpy.context.scene`

## master collection

`bpy.context.scene.collection`

> While the master collection contains all the Scene’s objects
> collections of Objects

## change active scene

```py
bpy.context.window.scene = bpy.data.scenes['Scene.001']
```

## view layer

`bpy.context.view_layer`

Collection をグループ化して可視制御する。
