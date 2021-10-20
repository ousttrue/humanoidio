# importer / exporter

```py
bl_info = {
    "name": "pyimpex",
    "author": "ousttrue",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "scene import and export",
    "doc_url": "https://github.com/ousttrue/pyimpex",
    "category": "Import-Export", # <= これ
    "support": "TESTING",
    "warning": "This addon is still in development.",
}
```

## Importer

```py
import bpy
from bpy_extras.io_utils import ImportHelper


class Importer(bpy.types.Operator, ImportHelper):
    bl_idname = "humanoidio.importer"
    bl_label = "Model Importer"
```

## Exporter

```py
class SomeImporter(bpy.types.Operator, ExportHelper):
    pass
```