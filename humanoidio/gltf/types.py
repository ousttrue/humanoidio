import ctypes


class Float3(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
    ]

    def __eq__(self, o: object) -> bool:
        return self.x == o.x and self.y == o.y and self.z == o.z


class Float4(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('w', ctypes.c_float),
    ]
