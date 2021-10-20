from typing import Optional, Generator, Any


class Submesh:
    def __init__(self, index_offset: int, index_count: int):
        self.index_offset = index_offset
        self.index_count = index_count
        self.vertex_offset = 0
        self.indices: Optional[Generator[Any, None, None]] = None
        self.POSITION: Optional[Generator[Any, None, None]] = None
        self.NORMAL: Optional[Generator[Any, None, None]] = None
        self.TEXCOORD_0: Optional[Generator[Any, None, None]] = None
        self.JOINTS_0: Optional[Generator[Any, None, None]] = None
        self.WEIGHTS_0: Optional[Generator[Any, None, None]] = None

    def set_attribute(self, key: str, value):
        if key == 'POSITION':
            self.POSITION = value
        elif key == 'NORMAL':
            self.NORMAL = value
        elif key == 'TEXCOORD_0':
            self.TEXCOORD_0 = value
        elif key == 'JOINTS_0':
            self.JOINTS_0 = value
        elif key == 'WEIGHTS_0':
            self.WEIGHTS_0 = value
        else:
            raise NotImplementedError()

    def get_vertices(self):
        pos = self.POSITION()
        nom = self.NORMAL()
        while True:
            try:
                p = next(pos)
                n = next(nom)
                yield p, n
            except StopIteration:
                break

    def get_indices(self):
        i = self.indices()
        while True:
            try:
                i0 = next(i)
                i1 = next(i)
                i2 = next(i)
                yield (i0, i1, i2)
            except StopIteration:
                break


class Mesh:
    def __init__(self, name: str):
        self.name = name
        self.submeshes = []
