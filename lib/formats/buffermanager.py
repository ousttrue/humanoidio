from typing import Optional, List, Callable, Tuple
import ctypes
from . import gltf
from .binarybuffer import BinaryBuffer
from .buffertypes import Vector3

MINMAX = Callable[[memoryview], List[float]]


def create_sparse_buffer(buffer: memoryview) -> Tuple[memoryview, memoryview]:
    Vector3Array = (Vector3 * len(buffer))
    vec3array = Vector3Array.from_buffer(buffer)

    index_list: List[int] = []
    for i, v in enumerate(vec3array):
        if v.x == 0 and v.y == 0 and v.z == 0:
            continue
        index_list.append(i)

    values = (Vector3 * len(index_list))()
    indices = (ctypes.c_int * len(index_list))()
    for i, index in enumerate(index_list):
        indices[i] = index
        values[i] = vec3array[index]

    if len(indices) == 0:
        indices = (ctypes.c_int * 1)()
        indices[0] = 0
        values = (Vector3 * 1)()
        values[0] = Vector3(0, 0, 0)

    return memoryview(indices), memoryview(values)


def format_to_componentType(t: str) -> Tuple[gltf.AccessorComponentType, int]:
    if t == 'f':
        return gltf.AccessorComponentType.FLOAT, 1
    elif t == 'I':
        return gltf.AccessorComponentType.UNSIGNED_INT, 1
    elif t == 'T{<f:x:<f:y:<f:z:}':
        return gltf.AccessorComponentType.FLOAT, 3
    elif t == 'T{<f:x:<f:y:}':
        return gltf.AccessorComponentType.FLOAT, 2
    elif t == 'T{<f:_11:<f:_12:<f:_13:<f:_14:<f:_21:<f:_22:<f:_23:<f:_24:<f:_31:<f:_32:<f:_33:<f:_34:<f:_41:<f:_42:<f:_43:<f:_44:}':  # noqa
        return gltf.AccessorComponentType.FLOAT, 16
    elif t == 'T{<H:x:<H:y:<H:z:<H:w:}':
        return gltf.AccessorComponentType.UNSIGNED_SHORT, 4
    elif t == 'T{<f:x:<f:y:<f:z:<f:w:}':
        return gltf.AccessorComponentType.FLOAT, 4
    else:
        raise NotImplementedError()


def accessortype_from_elementCount(count: int) -> gltf.AccessorType:
    if count == 1:
        return gltf.AccessorType.SCALAR
    elif count == 2:
        return gltf.AccessorType.VEC2
    elif count == 3:
        return gltf.AccessorType.VEC3
    elif count == 4:
        return gltf.AccessorType.VEC4
    elif count == 9:
        return gltf.AccessorType.MAT3
    elif count == 16:
        return gltf.AccessorType.MAT4
    else:
        raise NotImplementedError()


class BufferManager:
    def __init__(self):
        self.views: List[gltf.BufferView] = []
        self.accessors: List[gltf.Accessor] = []
        self.buffer = BinaryBuffer(0)

    def add_view(self, name: str, data: bytes) -> int:
        view_index = len(self.views)
        view = self.buffer.add_values(name, data)
        self.views.append(view)
        return view_index

    def push_bytes(self,
                   name: str,
                   values: memoryview,
                   min_max_pred: Optional[MINMAX] = None,
                   use_sparse=False) -> int:
        componentType, element_count = format_to_componentType(values.format)
        # append view
        view_index = self.add_view(name, values.tobytes())

        min = None
        max = None
        if min_max_pred:
            min, max = min_max_pred(values)

        if use_sparse:
            sparse_indices, sparse_values = create_sparse_buffer(values)

        if use_sparse and (sparse_indices.nbytes +
                           sparse_values.nbytes) < values.nbytes:
            # use sparse accessor
            sparse_indices_index = self.add_view(f'{name}.sparseIndices',
                                                 sparse_indices.tobytes())
            gltf_sparse_indices = gltf.AccessorSparseIndices(
                bufferView=sparse_indices_index,
                componentType=gltf.AccessorSparseIndicesComponentType.
                UNSIGNED_INT,
                extensions={},
                extras={})
            sparse_values_index = self.add_view(f'{name}.sparseValues',
                                                sparse_values.tobytes())
            gltf_sparse_values = gltf.AccessorSparseValues(
                bufferView=sparse_values_index, extensions={}, extras={})
            gltf_sparse = gltf.AccessorSparse(count=len(sparse_indices),
                                              indices=gltf_sparse_indices,
                                              values=gltf_sparse_values,
                                              extensions={},
                                              extras={})
            accessor_index = len(self.accessors)
            count = len(values)
            accessor = gltf.Accessor(
                name=name,
                bufferView=None,
                byteOffset=None,
                componentType=componentType,
                type=accessortype_from_elementCount(element_count),
                count=count,
                min=min,
                max=max,
                sparse=gltf_sparse,
                extensions={},
                extras={})
            self.accessors.append(accessor)
            return accessor_index

        else:
            accessor_index = len(self.accessors)
            count = len(values)
            accessor = gltf.Accessor(
                name=name,
                bufferView=view_index,
                byteOffset=0,
                componentType=componentType,
                type=accessortype_from_elementCount(element_count),
                count=count,
                min=min,
                max=max,
                extensions={},
                extras={})
            self.accessors.append(accessor)
            return accessor_index

