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

## TODO

* [ ] humanoid pose

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
* [ ] expression
* [ ] lookat
* [ ] VRM-1.0
* [x] collection

### VRM

元のツリー構成の維持には拘らない。

* Armature(Humanoid)
    * Mesh-0
    * Mesh-1
    * Mesh-2
    * Mesh-3...

という Ojbect 構成を強制する。

## bpy.props

RNAプロパティを定義して

* https://dskjal.com/blender/rna-vs-id-property.html
* https://docs.blender.org/api/2.83/bpy.props.html

UI(Panel)で表示する

* https://docs.blender.org/api/2.83/info_quickstart.html?highlight=panel#example-panel
* https://docs.blender.org/api/2.83/bpy.types.Panel.html?highlight=layout#bpy.types.Panel.layout

#### Meta
#### BlendShape
#### LookAt
#### FirstPerson
#### SpringBone

## Rigify の補助

[ ] Meta-rig を生成する補助

## Export

* [ ] Gltf, Vrm 別のエクスポーターに分ける
* [ ] material group を作るパネル
* [ ] unlit
* [x] PBR
* [ ] MToon
