import ctypes
from typing import Dict

from scene_translator.formats import gltf
from . import import_manager


class VertexBuffer:
    def __init__(self,
                 manager: import_manager.ImportManager,
                 mesh: gltf.Mesh)->None:
        # check shared attributes
        attributes: Dict[str, int] = {}
        shared = True
        for prim in mesh.primitives:
            # print(prim.attributes)
            if not attributes:
                attributes = prim.attributes
            else:
                if attributes != prim.attributes:
                    shared = False
                    break
        print(shared)

        #submeshes = [Submesh(path, gltf, prim) for prim in mesh.primitives]

        # merge submesh
        def position_count(prim):
            accessor_index = prim.attributes['POSITION']
            return manager.gltf.accessors[accessor_index].count
        pos_count = sum((position_count(prim) for prim in mesh.primitives), 0)
        self.pos = (ctypes.c_float * (pos_count * 3))()
        self.nom = (ctypes.c_float * (pos_count * 3))()
        self.uv = (import_manager.Float2 * pos_count)()
        self.joints = (import_manager.UShort4 * pos_count)()
        self.weights = (import_manager.Float4 * pos_count)()

        def index_count(prim: gltf.MeshPrimitive)->int:
            return manager.gltf.accessors[prim.indices].count
        index_count = sum((index_count(prim)  # type: ignore
                           for prim in mesh.primitives), 0)
        self.indices = (ctypes.c_int * index_count)()  # type: ignore
        self.submesh_index_count: List[int] = []

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
            pos = manager.get_array(prim.attributes['POSITION'])

            nom = None
            if 'NORMAL' in prim.attributes:
                nom = manager.get_array(prim.attributes['NORMAL'])
                if len(nom) != len(pos):
                    raise Exception("len(nom) different from len(pos)")

            uv = None
            if 'TEXCOORD_0' in prim.attributes:
                uv = manager.get_array(prim.attributes['TEXCOORD_0'])
                if len(uv) != len(pos):
                    raise Exception("len(uv) different from len(pos)")

            joints = None
            if 'JOINTS_0' in prim.attributes:
                joints = manager.get_array(prim.attributes['JOINTS_0'])
                if len(joints) != len(pos):
                    raise Exception("len(joints) different from len(pos)")

            weights = None
            if 'WEIGHTS_0' in prim.attributes:
                weights = manager.get_array(prim.attributes['WEIGHTS_0'])
                if len(weights) != len(pos):
                    raise Exception("len(weights) different from len(pos)")

            for p in pos:
                self.pos[pos_index] = p.x
                pos_index += 1
                self.pos[pos_index] = -p.z
                pos_index += 1
                self.pos[pos_index] = p.y
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
            indices = manager.get_array(prim.indices)
            for i in indices:
                self.indices[indices_index] = offset + i
                indices_index += 1

            self.submesh_index_count.append(len(indices))
            offset += len(pos)

    def get_submesh_from_face(self, face_index)->int:
        target = face_index*3
        n = 0
        for i, count in enumerate(self.submesh_index_count):
            n += count
            if target < n:
                return i
        return -1
