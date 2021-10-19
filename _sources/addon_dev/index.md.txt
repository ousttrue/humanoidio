# AddOn Dev

```{toctree}
articles
importer_exporter
```

## path
* `%APPDATA%\Blender Foundation\Blender\2.93\scripts\addons`

## module

`addons/ADDON.py` もしくは `addons/ADDON_DIR/__init__.py` に記述する。

blender の addon module は、`bl_info`, `register`, `unregister`
の３つの要素を持つ。

## bl_info

bl_info は module root の `.py` に直接記述されている必要がある。

```py
# こういうのは動かない
from hoge import bl_info
```

```
AST error parsing bl_info for: Traceback (most recent call last):
  File "2.93\scripts\modules\addon_utils.py", line 137, in fake_module
    mod.bl_info = ast.literal_eval(body.value)
```

* <https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo#Script_Meta_Info>
* <https://github.com/dfelinto/blender/blob/master/release/scripts/modules/addon_utils.py>

## register

```py
def register():
    # operators
    for c in CLASSES:
        bpy.utils.register_class(c)

    # bpy.ops.{c.bl_idname} という名の operator が登録される
    # bl_idname = "SOME.OPERATOR" の場合
    # bpy.ops.SOME.OPERATOR() と実行できる

    # menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)  # type: ignore
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)  # type: ignore
```

## unregister

```py
def unregister():
    # Note: when unregister, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for c in CLASSES:
        bpy.utils.unregister_class(c)

    # menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)  # type: ignore
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)  # type: ignore
```
