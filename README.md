# pyimpex

python import export.

for Blender-2.83

```
    Deserialize             Import
+----+   +-------------+----------------> +-----+
|gltf|-->| SubmeshMesh |   +--------+     | bpy |
|    |<--|             |<--|FaceMesh| <-- |     |
+----+   +-------------+   +--------+     +-----+
    Serialize               Export
```

* VRMは armature がひとつ(Humanoid)しかない前提にする
* 手前向き T-Pose で作成する
* modifier(Generate) の上から作った shapekey をそのままエクスポートできる。Apply も不要
* object.location, rotation, scale を apply する
  * objectの親子あってもapplyできる
  * blenderのZ-UP右手系を、決め打ちでGLTFのY-UP右手系に変換する。ルート付近に X90度回転を残さない

## reference

* https://docs.blender.org/manual/en/2.83/
  * https://docs.blender.org/manual/en/2.83/advanced/scripting/addon_tutorial.html
* https://docs.blender.org/api/2.83/index.html

* addons/io_scene_gltf2

## 座標系

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

## VRM Object構成

元のツリー構成の維持には拘らない。
単一の Armature に複数の Mesh が乗る。

* Armature(Humanoid)
    * Mesh-0
    * Mesh-1
    * Mesh-2
    * Mesh-3...

## Import

* [x] remove empty VertexGroup
* [x] remove leaf bone without bone weight
* [x] humanoid
* [x] rename humanoid bone
* [x] bone group
* [x] armature 一個にまとめる
* [x] MToon
* [x] 手前向きにする
* [x] Import: ShapeKey の無いところは SubMesh を別オブジェクトに分割する
* [x] expression
* [ ] lookat
* [ ] VRM-1.0
* [x] collection
* [ ] meta
* [ ] firstperson
* [ ] springbone
* [ ] rigify 自動生成
* [ ] humanoid pose
* [ ] 名前のマッピング。.001等がついて違う名前になったときの対応
* [ ] node の削除条件
  * 使われていない
    * 自分か子孫に
      * joint で無い(weight の無い joint は除去できるがめんどくさい)
      * mesh が無い
      * humanoid bone でない

## Export

* [ ] Gltf, Vrm 別のエクスポーターに分ける
* [ ] unlit
* [x] PBR
* [ ] MToon

## VRMの新規作成/memo

* [ ] material group
* [ ] modifier を適用せずにエクスポートする
* [ ] view位置をbookmarkする


## Rigify

* [ ] knee axis
* [ ] finger axis

```py
import bpy


def traverse(bl_bone: bpy.types.PoseBone, level=0):
    indent = '  ' * level

    if bl_bone.rigify_type:
        print(f'{indent}{bl_bone} => {bl_bone.rigify_type}')

    for child in bl_bone.children:
        traverse(child, level + 1)


def process(bl_obj: bpy.types.Object):
    # bl_armature = bl_obj.data
    print(bl_obj)
    for b in bl_obj.pose.bones:
        if not b.parent:
            traverse(b)


active = bpy.context.object
# active = bpy.context.view_layer.objects.active

process(active)
```

```
<bpy_struct, PoseBone("spine")> => spines.basic_spine
        <bpy_struct, PoseBone("spine.004")> => spines.super_head
              <bpy_struct, PoseBone("face")> => faces.super_face
        <bpy_struct, PoseBone("shoulder.L")> => basic.super_copy
          <bpy_struct, PoseBone("upper_arm.L")> => limbs.super_limb
                <bpy_struct, PoseBone("palm.01.L")> => limbs.super_palm
                  <bpy_struct, PoseBone("f_index.01.L")> => limbs.super_finger
                  <bpy_struct, PoseBone("thumb.01.L")> => limbs.super_finger
                  <bpy_struct, PoseBone("f_middle.01.L")> => limbs.super_finger
                  <bpy_struct, PoseBone("f_ring.01.L")> => limbs.super_finger
                  <bpy_struct, PoseBone("f_pinky.01.L")> => limbs.super_finger
        <bpy_struct, PoseBone("shoulder.R")> => basic.super_copy
          <bpy_struct, PoseBone("upper_arm.R")> => limbs.super_limb
                <bpy_struct, PoseBone("palm.01.R")> => limbs.super_palm
                  <bpy_struct, PoseBone("f_index.01.R")> => limbs.super_finger
                  <bpy_struct, PoseBone("thumb.01.R")> => limbs.super_finger
                  <bpy_struct, PoseBone("f_middle.01.R")> => limbs.super_finger
                  <bpy_struct, PoseBone("f_ring.01.R")> => limbs.super_finger
                  <bpy_struct, PoseBone("f_pinky.01.R")> => limbs.super_finger
        <bpy_struct, PoseBone("breast.L")> => basic.super_copy
        <bpy_struct, PoseBone("breast.R")> => basic.super_copy
  <bpy_struct, PoseBone("pelvis.L")> => basic.super_copy
  <bpy_struct, PoseBone("pelvis.R")> => basic.super_copy
  <bpy_struct, PoseBone("thigh.L")> => limbs.super_limb
  <bpy_struct, PoseBone("thigh.R")> => limbs.super_limb
```
