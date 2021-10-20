# mode

<https://toofu0.hatenablog.com/entry/2020/10/10/033418>

## currentmode

```py
print(bpy.context.object.mode)
```

## editmode

```py
bpy.ops.object.mode_set(mode='EDIT')
```

## objectmode

```py
bpy.ops.object.mode_set(mode='OBJECT')
```

## sample

```py
from contextlib import contextmanager
@contextmanager
def enter_edit_mode():
    # enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        yield
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
```
