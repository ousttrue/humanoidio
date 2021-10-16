# module

blender の addon module は、`bl_info`, `register`, `unregister`
の３つの要素を持つ。

bl_info は root の `__init__.py` に直接記述されている必要がある。

```py
# こういうのは動かない
from hoge import bl_info
```

```
AST error parsing bl_info for: Traceback (most recent call last):
  File "2.93\scripts\modules\addon_utils.py", line 137, in fake_module
    mod.bl_info = ast.literal_eval(body.value)
```
