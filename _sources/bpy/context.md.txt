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

## active object

```py
# これ
bpy.context.active_object # readonly

# active_object と object 同じぽい？
bpy.context.object # readonly

# change
bpy.context.scene.objects.active
```

https://blender.stackexchange.com/questions/31759/are-bpy-context-object-and-bpy-context-active-object-still-the-same
`context.object == context.active_object ?`

```py
# 2.80
bpy.context.view_layer.objects.active = obj 
# 2.79
bpy.context.scene.objects.active = obj
```

## selected object

`bpy.context.selected_objects`

```py
# 2.8
obj.select_set(True)
# 2.79
obj.select = True
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
