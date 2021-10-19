# BMesh

* <https://docs.blender.org/api/current/bmesh.html>
    * <https://wiki.blender.org/wiki/Source/Modeling/BMesh/Design>
    * <https://blender.stackexchange.com/questions/63546/create-a-cube-in-blender-from-python>

* 2018 [Blender Python BMesh 〜点の操作〜](http://takunoji.hatenablog.com/entry/2018/03/26/225317)
* 2018 [Blender Python 開発メモ 〜UV座標の取得〜](http://takunoji.hatenablog.com/entry/2018/03/20/221150)


### create cube

```py
import bmesh
```

## empty

```py
# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
```

## from_mesh

```py
# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(mesh)   # fill it in from a Mesh
```

## from_edit_mesh

## apply

```py
# Finish up, write the bmesh back to the mesh
bm.to_mesh(mesh)
bm.free()  # free and prevent further access
```
