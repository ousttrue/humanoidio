from lib.formats.buffertypes import Vector3
from logging import getLogger
logger = getLogger(__name__)
import enum
import ctypes
from lib.yup.submesh_mesh import SubmeshMesh
from typing import List, Dict
import bpy, mathutils
from .formats import gltf
from .formats import GltfContext
from .yup import Node
from .struct_types import Float2, Float3, Float4, UShort4


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


class VertexBuffer:
    def __init__(self, data: GltfContext, mesh_index: int):
        # check shared attributes
        attributes: Dict[str, int] = {}
        shared = True

        mesh = data.gltf.meshes[mesh_index]
        for prim in mesh.primitives:
            if not attributes:
                attributes = prim.attributes
            else:
                if attributes != prim.attributes:
                    shared = False
                    break
        logger.debug(f'SHARED: {shared}')

        #submeshes = [Submesh(path, gltf, prim) for prim in mesh.primitives]

        # merge submesh
        def position_count(prim):
            accessor_index = prim.attributes['POSITION']
            return data.gltf.accessors[accessor_index].count

        pos_count = sum((position_count(prim) for prim in mesh.primitives), 0)

        self.pos = (Float3 * pos_count)()
        self.nom = (ctypes.c_float * (pos_count * 3))()
        self.uv = (Float2 * pos_count)()
        self.joints = (UShort4 * pos_count)()
        self.weights = (Float4 * pos_count)()

        def prim_index_count(prim: gltf.MeshPrimitive) -> int:
            if not isinstance(prim.indices, int):
                return 0
            return data.gltf.accessors[prim.indices].count

        index_count = sum((prim_index_count(prim) for prim in mesh.primitives),
                          0)
        self.indices = (ctypes.c_int * index_count)()
        self.submesh_index_count: List[int] = []

        reader = BytesReader(data)

        pos_index = 0
        nom_index = 0
        uv_index = 0
        indices_index = 0
        offset = 0
        joint_index = 0
        for prim in mesh.primitives:
            #
            # attributes
            #
            pos = reader.get_bytes(prim.attributes['POSITION'])

            nom = None
            if 'NORMAL' in prim.attributes:
                nom = reader.get_bytes(prim.attributes['NORMAL'])
                if len(nom) != len(pos):
                    raise Exception("len(nom) different from len(pos)")

            uv = None
            if 'TEXCOORD_0' in prim.attributes:
                uv = reader.get_bytes(prim.attributes['TEXCOORD_0'])
                if len(uv) != len(pos):
                    raise Exception("len(uv) different from len(pos)")

            joints = None
            if 'JOINTS_0' in prim.attributes:
                joints = reader.get_bytes(prim.attributes['JOINTS_0'])
                if len(joints) != len(pos):
                    raise Exception("len(joints) different from len(pos)")

            weights = None
            if 'WEIGHTS_0' in prim.attributes:
                weights = reader.get_bytes(prim.attributes['WEIGHTS_0'])
                if len(weights) != len(pos):
                    raise Exception("len(weights) different from len(pos)")

            for p in pos:
                self.pos[pos_index].x = p.x
                self.pos[pos_index].y = -p.z
                self.pos[pos_index].z = p.y
                pos_index += 1

            if nom:
                for n in nom:
                    self.nom[nom_index] = n.x
                    nom_index += 1
                    self.nom[nom_index] = -n.z
                    nom_index += 1
                    self.nom[nom_index] = n.y
                    nom_index += 1

            if uv:
                for xy in uv:
                    xy.y = 1.0 - xy.y  # flip vertical
                    self.uv[uv_index] = xy
                    uv_index += 1

            if joints and weights:
                for joint, weight in zip(joints, weights):
                    self.joints[joint_index] = joint
                    self.weights[joint_index] = weight
                    joint_index += 1

            #
            # indices
            #
            if not isinstance(prim.indices, int):
                raise Exception()
            indices = reader.get_bytes(prim.indices)
            for i in indices:
                self.indices[indices_index] = offset + i
                indices_index += 1

            self.submesh_index_count.append(len(indices))
            offset += len(pos)

    def get_submesh_from_face(self, face_index) -> int:
        target = face_index * 3
        n = 0
        for i, count in enumerate(self.submesh_index_count):
            n += count
            if target < n:
                return i
        return -1


def load_submesh(data: GltfContext, mesh_index: int) -> SubmeshMesh:
    m = data.gltf.meshes[mesh_index]
    name = m.name if m.name else f'mesh {mesh_index}'
    mesh = SubmeshMesh(name)

    vb = VertexBuffer(data, mesh_index)
    mesh.positions = memoryview(vb.pos)

    return mesh


def import_submesh(data: GltfContext) -> List[Node]:
    '''
    glTFを中間形式のSubmesh形式に変換する
    '''
    meshes: List[SubmeshMesh] = []
    if data.gltf.meshes:
        for i, m in enumerate(data.gltf.meshes):
            mesh = load_submesh(data, i)
            meshes.append(mesh)

    nodes: List[Node] = []
    if data.gltf.nodes:
        for i, n in enumerate(data.gltf.nodes):
            name = n.name if n.name else f'node {i}'
            node = Node(name)

            if n.translation:
                node.position.x = n.translation[0]
                node.position.y = n.translation[1]
                node.position.z = n.translation[2]

            if n.rotation:
                node.rotation.x = n.rotation[0]
                node.rotation.y = n.rotation[1]
                node.rotation.z = n.rotation[2]
                node.rotation.w = n.rotation[3]

            if n.scale:
                node.scale.x = n.scale[0]
                node.scale.y = n.scale[1]
                node.scale.z = n.scale[2]

            if n.matrix:
                m = n.matrix
                matrix = mathutils.Matrix(
                    ((m[0], m[4], m[8], m[12]), (m[1], m[5], m[9], m[13]),
                     (m[2], m[6], m[10], m[14]), (m[3], m[7], m[11], m[15])))
                t, q, s = matrix.decompose()
                node.position.x = t.x
                node.position.y = t.y
                node.position.z = t.z
                node.rotation.x = q.x
                node.rotation.y = q.y
                node.rotation.z = q.z
                node.rotation.w = q.w
                node.scale.x = s.x
                node.scale.y = s.y
                node.scale.z = s.z

            if isinstance(n.mesh, int):
                node.mesh = meshes[n.mesh]

            nodes.append(node)

        for i, n in enumerate(data.gltf.nodes):
            if n.children:
                for c in n.children:
                    nodes[i].add_child(nodes[c])

    scene = data.gltf.scenes[data.gltf.scene if data.gltf.scene else 0]
    if not scene.nodes:
        return []

    return [nodes[root] for root in scene.nodes]
