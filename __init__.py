from .humanoidio import (register, unregister)
bl_info = {
    "name": "humanoidio",
    "blender": (2, 93, 0),
    "category": "Import-Export",
    "support": "TESTING",
}

if "humanoidio" in locals():
    import importlib
    import sys
    tmp = {k: v for k, v in sys.modules.items()}
    for k, m in tmp.items():
        if k.startswith('humanoidio.'):
            importlib.reload(m)
