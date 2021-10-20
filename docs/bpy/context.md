# bpy.context

<https://docs.blender.org/api/current/bpy.context.html>

* context
    * window
        * scene => data hierarchy
            * view_layers
                * collection
        * workspace => GUI layout

## scene

```py
# read
bpy.context.scene
# change
bpy.context.window.scene = bpy.data.scenes['Scene.001']
```


## mode

`bpy.context.object.mode`

## bpy.context.area

[【Blender 2.8 アドオン開発】003 Blender 内のデータにアクセスしよう(Context と データ構造 と レイアウト) ](https://memoteu.hatenablog.com/entry/2019/04/02/041803)

## Contextオーバーライド

<https://docs.blender.org/api/blender2.8/bpy.ops.html#overriding-context>

```py
# remove all objects in scene rather than the selected ones
import bpy
override = bpy.context.copy()
override['selected_objects'] = list(bpy.context.scene.objects)
bpy.ops.object.delete(override)
```

## window

```py
bpy.context.window
window.workspace # 画面レイアウト
workspace.screens # blender 各window. main window と preference window など
screen.area # 分割された区画
area.type == 'INFO'
area.region # 区画内の部分
# region 内に panel が配置される
```
