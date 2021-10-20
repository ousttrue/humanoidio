# BMesh

* <https://docs.blender.org/api/current/bmesh.html>
    * <https://wiki.blender.org/wiki/Source/Modeling/BMesh/Design>

## basic

```py
import bmesh
```

### create empty

```py
# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
```

### load from mesh


```py
bm.from_mesh(mesh) 
```
### apply to mesh

```py
# Finish up, write the bmesh back to the mesh
bm.to_mesh(mesh)
bm.free()  # free and prevent further access
```

## vertex

* [Blender Python BMesh 〜点の操作〜](http://takunoji.hatenablog.com/entry/2018/03/26/225317)

### add

```py
v = bm.verts.new((x, y, z))
```

## loop layer
### uv_layer

* [Blender Python 開発メモ 〜UV座標の取得〜](http://takunoji.hatenablog.com/entry/2018/03/20/221150)

`loop` の `UV layer` に格納されている。
`vert` から接続する `loop` を得て、その `uv layer` から値を得る。

```py
uv_layer = bm.loops.layers.uv.new(UV_LAYER_NAME)
```

```py
layer = bm.loops.layers.uv.active

def uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        return l[uv_layer].uv
    return None
```

## verts layer
### vertex group

* [Manipulate vertex groups via bmesh?](https://devtalk.blender.org/t/manipulate-vertex-groups-via-bmesh/11192)

* <https://blender.stackexchange.com/questions/69426/accessing-weights-of-a-bmesh>

```py
layer = bm.verts.layers.deform.active
```

### morph target

```py
layer = bm.verts.layers.shape.new(target.name)
```
