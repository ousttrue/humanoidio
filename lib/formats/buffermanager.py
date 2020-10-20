from logging import getLogger
logger = getLogger(__name__)
from typing import Optional, List, Callable, Tuple
import ctypes
from . import gltf
from .binarybuffer import BinaryBuffer
from .gltf_context import GltfContext
from ..struct_types import PlanarBuffer, Float2, Float3, Float4, UShort4
from ..pyscene.submesh_mesh import SubmeshMesh, Submesh, Material

MINMAX = Callable[[memoryview], List[float]]


def create_sparse_buffer(buffer: memoryview) -> Tuple[memoryview, memoryview]:
    Vector3Array = (Float3 * len(buffer))
    vec3array = Vector3Array.from_buffer(buffer)

    index_list: List[int] = []
    for i, v in enumerate(vec3array):
        if v.x == 0 and v.y == 0 and v.z == 0:
            continue
        index_list.append(i)

    values = (Float3 * len(index_list))()
    indices = (ctypes.c_int * len(index_list))()
    for i, index in enumerate(index_list):
        indices[i] = index
        values[i] = vec3array[index]

    if len(indices) == 0:
        indices = (ctypes.c_int * 1)()
        indices[0] = 0
        values = (Float3 * 1)()
        values[0] = Float3(0, 0, 0)

    return memoryview(indices), memoryview(values)


def format_to_componentType(values: memoryview) -> Tuple[gltf.AccessorComponentType, int]:
    t = values.format
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

    if values.itemsize == 8:
        return gltf.AccessorComponentType.FLOAT, 2
    if values.itemsize == 12:
        return gltf.AccessorComponentType.FLOAT, 3
    if values.itemsize == 16:
        return gltf.AccessorComponentType.FLOAT, 4

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
        componentType, element_count = format_to_componentType(values)
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


def get_accessor_type_to_count(accessor_type: gltf.AccessorType) -> int:
    if accessor_type == gltf.AccessorType.SCALAR:
        return 1
    elif accessor_type == gltf.AccessorType.VEC2:
        return 2
    elif accessor_type == gltf.AccessorType.VEC3:
        return 3
    elif accessor_type == gltf.AccessorType.VEC4:
        return 4
    elif accessor_type == gltf.AccessorType.MAT2:
        return 4
    elif accessor_type == gltf.AccessorType.MAT3:
        return 9
    elif accessor_type == gltf.AccessorType.MAT4:
        return 16
    else:
        raise Exception()


def get_accessor_component_type_to_len(
        component_type: gltf.AccessorComponentType) -> int:
    if component_type == gltf.AccessorComponentType.BYTE:
        return 1
    elif component_type == gltf.AccessorComponentType.SHORT:
        return 2
    elif component_type == gltf.AccessorComponentType.UNSIGNED_BYTE:
        return 1
    elif component_type == gltf.AccessorComponentType.UNSIGNED_SHORT:
        return 2
    elif component_type == gltf.AccessorComponentType.UNSIGNED_INT:
        return 4
    elif component_type == gltf.AccessorComponentType.FLOAT:
        return 4
    else:
        raise NotImplementedError()


def get_accessor_byteslen(accessor: gltf.Accessor) -> int:
    return (accessor.count * get_accessor_type_to_count(accessor.type) *
            get_accessor_component_type_to_len(accessor.componentType))


class BytesReader:
    def __init__(self, data: GltfContext):
        self.data = data
        # gltf の url 参照の外部ファイルバッファをキャッシュする
        self._buffer_map: Dict[str, bytes] = {}
        self._material_map: Dict[int, Material] = {}

    def get_view_bytes(self, view_index: int) -> bytes:
        view = self.data.gltf.bufferViews[view_index]
        buffer = self.data.gltf.buffers[view.buffer]
        if buffer.uri:
            if buffer.uri in self._buffer_map:
                return self._buffer_map[
                    buffer.uri][view.byteOffset:view.byteOffset +
                                view.byteLength]
            else:
                path = self.data.dir / buffer.uri
                with path.open('rb') as f:
                    data = f.read()
                    self._buffer_map[buffer.uri] = data
                    return data[view.byteOffset:view.byteOffset +
                                view.byteLength]
        else:
            return self.data.bin[view.byteOffset:view.byteOffset +
                                 view.byteLength]

    def get_bytes(self, accessor_index: int):
        accessor = self.data.gltf.accessors[
            accessor_index] if self.data.gltf.accessors else None
        if not accessor:
            raise Exception()
        accessor_byte_len = get_accessor_byteslen(accessor)
        if not isinstance(accessor.bufferView, int):
            raise Exception()
        view_bytes = self.get_view_bytes(accessor.bufferView)
        segment = view_bytes[accessor.byteOffset:accessor.byteOffset +
                             accessor_byte_len]

        if accessor.type == gltf.AccessorType.SCALAR:
            if (accessor.componentType == gltf.AccessorComponentType.SHORT
                    or accessor.componentType
                    == gltf.AccessorComponentType.UNSIGNED_SHORT):
                return (ctypes.c_ushort *  # type: ignore
                        accessor.count).from_buffer_copy(segment)
            elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_INT:
                return (ctypes.c_uint *  # type: ignore
                        accessor.count).from_buffer_copy(segment)
        elif accessor.type == gltf.AccessorType.VEC2:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float2 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        elif accessor.type == gltf.AccessorType.VEC3:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float3 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        elif accessor.type == gltf.AccessorType.VEC4:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float4 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

            elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_SHORT:
                return (UShort4 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        elif accessor.type == gltf.AccessorType.MAT4:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Mat16 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

        raise NotImplementedError()

    def get_or_create_material(self,
                               material_index: Optional[int]) -> Material:
        if not isinstance(material_index, int):
            return Material(f'default')
        material = self._material_map.get(material_index)
        if not material:
            material = Material(f'material{material_index}')
            self._material_map[material_index] = material
        return material

    def read_attributes(self, buffer: PlanarBuffer, offset: int,
                        data: GltfContext, prim: gltf.MeshPrimitive):
        self.submesh_index_count: List[int] = []

        pos_index = offset
        nom_index = offset
        uv_index = offset
        indices_index = offset
        joint_index = offset

        #
        # attributes
        #
        pos = self.get_bytes(prim.attributes['POSITION'])

        nom = None
        if 'NORMAL' in prim.attributes:
            nom = self.get_bytes(prim.attributes['NORMAL'])
            if len(nom) != len(pos):
                raise Exception("len(nom) different from len(pos)")

        uv = None
        if 'TEXCOORD_0' in prim.attributes:
            uv = self.get_bytes(prim.attributes['TEXCOORD_0'])
            if len(uv) != len(pos):
                raise Exception("len(uv) different from len(pos)")

        joints = None
        if 'JOINTS_0' in prim.attributes:
            joints = self.get_bytes(prim.attributes['JOINTS_0'])
            if len(joints) != len(pos):
                raise Exception("len(joints) different from len(pos)")

        weights = None
        if 'WEIGHTS_0' in prim.attributes:
            weights = self.get_bytes(prim.attributes['WEIGHTS_0'])
            if len(weights) != len(pos):
                raise Exception("len(weights) different from len(pos)")

        for p in pos:
            # to zup
            buffer.position[pos_index].x = p.x
            buffer.position[pos_index].y = -p.z
            buffer.position[pos_index].z = p.y
            pos_index += 1

        if nom:
            for n in nom:
                # to zup
                buffer.normal[nom_index].x = n.x
                buffer.normal[nom_index].y = -n.z
                buffer.normal[nom_index].z = n.y
                nom_index += 1

        if uv:
            for xy in uv:
                xy.y = 1.0 - xy.y  # flip vertical
                buffer.texcoord[uv_index] = xy
                uv_index += 1

        if joints and weights:
            for joint, weight in zip(joints, weights):
                buffer.joints[joint_index] = joint
                buffer.weights[joint_index] = weight
                joint_index += 1

    def load_submesh(self, data: GltfContext, mesh_index: int) -> SubmeshMesh:
        m = data.gltf.meshes[mesh_index]
        name = m.name if m.name else f'mesh {mesh_index}'

        # check shared attributes
        shared = True
        attributes: Dict[str, int] = {}
        for prim in m.primitives:
            if not attributes:
                attributes = prim.attributes
            else:
                if attributes != prim.attributes:
                    shared = False
                    break
        logger.debug(f'SHARED: {shared}')

        def position_count(prim):
            accessor_index = prim.attributes['POSITION']
            return data.gltf.accessors[accessor_index].count

        def prim_index_count(prim: gltf.MeshPrimitive) -> int:
            if not isinstance(prim.indices, int):
                return 0
            return data.gltf.accessors[prim.indices].count

        buffer: Optional[PlanarBuffer] = None

        def add_indices(sm: SubmeshMesh, prim: gltf.MeshPrimitive,
                        index_offset: int):
            # indices
            if not isinstance(prim.indices, int):
                raise Exception()
            mesh.indices.extend(self.get_bytes(prim.indices))
            # submesh
            index_count = prim_index_count(prim)
            submesh = Submesh(index_offset, index_count,
                              self.get_or_create_material(prim.material))
            mesh.submeshes.append(submesh)
            return index_count

        has_bone_weight = False

        if shared:
            # share vertex buffer
            vertex_count = position_count(m.primitives[0])
            mesh = SubmeshMesh(name, vertex_count, has_bone_weight)
            self.read_attributes(mesh.attributes, 0, data, m.primitives[0])

            index_offset = 0
            for i, prim in enumerate(m.primitives):
                # indices
                index_offset += add_indices(mesh, prim, index_offset)
        else:
            # merge vertex buffer
            vertex_count = sum((position_count(prim) for prim in m.primitives),
                               0)
            mesh = SubmeshMesh(name, vertex_count, has_bone_weight)

            offset = 0
            index_offset = 0
            for i, prim in enumerate(m.primitives):
                # vertex
                self.read_attributes(mesh.attributes, offset, data, prim)
                offset += position_count(prim)
                # indices
                index_offset += add_indices(mesh, prim, index_offset)

        return mesh
