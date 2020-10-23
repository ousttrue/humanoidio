from typing import Dict, List
import ctypes
from ..struct_types import PlanarBuffer, Float2, Float3, Float4, UShort4
from .. import formats
from ..formats import gltf


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
    def __init__(self, data: formats.GltfContext):
        self.data = data
        self._buffer_map: Dict[str, bytes] = {}

    def get_view_bytes(self, view_index: int) -> bytes:
        view = self.data.gltf.bufferViews[view_index]
        buffer = self.data.gltf.buffers[view.buffer]
        if buffer.uri:
            if buffer.uri in self._buffer_map:
                data = self._buffer_map[buffer.uri]
                offset = view.byteOffset if view.byteOffset else 0
                return data[offset:offset + view.byteLength]
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
        byteOffset = accessor.byteOffset if isinstance(accessor.byteOffset,
                                                       int) else 0
        segment = view_bytes[byteOffset:byteOffset + accessor_byte_len]

        if accessor.type == gltf.AccessorType.SCALAR:
            if (accessor.componentType == gltf.AccessorComponentType.BYTE
                    or accessor.componentType
                    == gltf.AccessorComponentType.UNSIGNED_BYTE):
                return (ctypes.c_ubyte *
                        accessor.count).from_buffer_copy(segment)
            elif (accessor.componentType == gltf.AccessorComponentType.SHORT
                  or accessor.componentType
                  == gltf.AccessorComponentType.UNSIGNED_SHORT):
                return (ctypes.c_ushort *
                        accessor.count).from_buffer_copy(segment)
            elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_INT:
                return (ctypes.c_uint *
                        accessor.count).from_buffer_copy(segment)

            raise NotImplementedError()

        elif accessor.type == gltf.AccessorType.VEC2:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float2 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)
            raise NotImplementedError()

        elif accessor.type == gltf.AccessorType.VEC3:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float3 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)
            raise NotImplementedError()

        elif accessor.type == gltf.AccessorType.VEC4:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Float4 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

            elif accessor.componentType == gltf.AccessorComponentType.UNSIGNED_SHORT:
                return (UShort4 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)

            raise NotImplementedError()

        elif accessor.type == gltf.AccessorType.MAT4:
            if accessor.componentType == gltf.AccessorComponentType.FLOAT:
                return (Mat16 *  # type: ignore
                        accessor.count).from_buffer_copy(segment)
            raise NotImplementedError()

        raise NotImplementedError()

    def read_attributes(self, buffer: PlanarBuffer, offset: int,
                        data: formats.GltfContext, prim: gltf.MeshPrimitive):
        self.submesh_index_count: List[int] = []

        pos_index = offset
        nom_index = offset
        uv_index = offset
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
            buffer.position[pos_index] = p
            pos_index += 1

        if nom:
            for n in nom:
                buffer.normal[nom_index] = n
                nom_index += 1

        if uv:
            for xy in uv:
                buffer.texcoord[uv_index] = xy
                uv_index += 1

        if joints and weights:
            for joint, weight in zip(joints, weights):
                buffer.joints[joint_index] = joint
                buffer.weights[joint_index] = weight
                joint_index += 1
