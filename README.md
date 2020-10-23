# scene_translator

import/export for Blender-2.83

## reference

* https://docs.blender.org/manual/en/2.83/
  * https://docs.blender.org/manual/en/2.83/advanced/scripting/addon_tutorial.html
* https://docs.blender.org/api/2.83/index.html

## pillow install

```bat
# run as administrator
> cd 'C:\Program Files\Blender Foundation\Blender 2.83\2.83\python\bin\'
> .\python -m pip install --upgrade pip
> .\python.exe -m pip install pillow
```

## memo

```
    Deserialize             Import
+----+   +-------------+----------------> +-----+
|gltf|-->| SubmeshMesh |   +--------+     | bpy |
|    |<--|             |<--|FaceMesh| <-- |     |
+----+   +-------------+   +--------+     +-----+
    Serialize               Export
```

* 手前向き T-Pose で作成する
* modifier の上から作った shapekey をそのままエクスポートできる。Apply も不要
* object.location, rotation, scale を apply する
  * objectの親子あってもapplyできる
  * blenderのZ-UP右手系を、決め打ちでGLTFのY-UP右手系に変換する。ルート付近に X90度回転を残さない

### Import

* gltf -> submesh: Y-UP, TopLeft-Origin
* submesh -> bpy: Z-UP, BottomLeft-Origin

### Export

* bpy -> facemesh: Z-UP, BottomLeft-Origin
* facemesh -> submesh: Y-UP, TopLeft-Origin
* submesh -> gltf: Y-UP, TopLeft-Origin

## TODO

* [ ] BMesh
* [x] remove empty
* [x] blend mode
* [x] alpha cutout
* [x] Unlit Transparent
* [x] Standard Transparent
* [ ] shape key
* [ ] texture/uv flip flip

### VRM

* [ ] VRM
* [ ] armature 一個にまとめる
* [ ] MToon

## 仕様

Blender側でVRMの追加情報をどのように保持するかなど

### 座標系

* blenderのZ-UP右手系を、決め打ちでGLTFのY-UP右手系に変換する

``` py
    def from_Vector(v: mathutils.Vector) -> 'Float3':
        # Float3(v.x, v.z, -v.y) # Y-UP
        # Float3(-v.x, v.z, v.y) # rotate 180 degrees by Y axis
        return Float3(-v.x, v.z, v.y)
```

``` 
T-Pose手前向き     => T-Pose奥向き

Z          Y               Y
^          ^               ^
|  + Y     |               |  + Z
| /        |               | /
|/         |               |/
+----> X   +----> X X <----+
Blender   /GLTF            rotate 180 degrees by Y axis
         /
        L Z
```

### Humanoid

Humanoidを表す Armature の `bpy.types.Bone` にカスタムプロパティ `humanoid_bone` を追加して、
そこにヒューマノイド情報を記録する。

``` py
bpy.types.Bone.humanoid_bone = EnumProperty(
        name="humanoid",
        items=[('none', 'none', '')] + [(bone.name, bone.name, '')
                                        for bone in HumanoidBones])
```

![CustomProperty](documents/humanoid_bone.jpg)

![設定パネル](documents/humanoid_armature.jpg)

### Meta

Humanoidを記録するArmatureの IDProperty に文字列で記録する。

![CustomProperty](documents/meta_custom_property.jpg)

![設定パネル](documents/meta_panel.jpg)

### Material

TODO

### FirstPerson

TODO

### BlendShape

TODO

### LookAt

TODO

### SpringBone

TODO

