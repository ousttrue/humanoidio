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
* [ ] vrm meta thumbnail

## Export

* [ ] Gltf, Vrm 別のエクスポーターに分ける
* [ ] unlit
* [x] PBR
* [ ] MToon
* [ ] skinning
* [ ] vrm humanoid
* [ ] vrm meta

## VRMの新規作成

* [ ] material group
* [ ] modifier を適用せずにエクスポートする

## Memo

* [x] view位置をbookmarkする。 `VIEW_3D`

## lookat

* Armature に `Yaw, Pitch` プロパティを作ってそこから駆動できるか？

## Rigify

* [ ] knee axis
* [ ] finger axis
