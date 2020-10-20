from logging import getLogger
logger = getLogger(__name__)
import ctypes
from typing import Dict, Optional, List
from ..struct_types import PlanarBuffer, Float2, Float3
from ..formats import gltf
from ..formats.gltf_context import GltfContext
from ..pyscene.submesh_mesh import SubmeshMesh, Submesh
from ..pyscene.material import Material, PBRMaterial, Texture


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
        byteOffset = accessor.byteOffset if isinstance(accessor.byteOffset,
                                                       int) else 0
        segment = view_bytes[byteOffset:byteOffset + accessor_byte_len]

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
        if material:
            return material

        # create
        gl_material = self.data.gltf.materials[material_index]
        if gl_material.extensions and 'KHR_materials_unlit' in gl_material.extensions:
            material = Material(f'material{material_index}')
        else:
            material = PBRMaterial(f'material{material_index}')
        self._material_map[material_index] = material

        # color
        if gl_material.pbrMetallicRoughness.baseColorFactor:
            material.color.x = gl_material.pbrMetallicRoughness.baseColorFactor[
                0]
            material.color.y = gl_material.pbrMetallicRoughness.baseColorFactor[
                1]
            material.color.z = gl_material.pbrMetallicRoughness.baseColorFactor[
                2]
            material.color.w = gl_material.pbrMetallicRoughness.baseColorFactor[
                3]
        # texture
        if gl_material.pbrMetallicRoughness.baseColorTexture:
            gl_image = self.data.gltf.images[
                gl_material.pbrMetallicRoughness.baseColorTexture.index]
            image_bytes = self.get_view_bytes(
                gl_material.pbrMetallicRoughness.baseColorTexture.index)
            name = f'texture{gl_material.pbrMetallicRoughness.baseColorTexture.index}'
            if gl_image.name:
                name = gl_image.name
            material.texture = Texture(name, image_bytes)

        return material

    def read_attributes(self, buffer: PlanarBuffer, offset: int,
                        data: GltfContext, prim: gltf.MeshPrimitive):
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
