from typing import List, Optional, Dict, Iterable
import ctypes
from .bytesreader import BytesReader
from .buffer_types import Vertex4BoneWeights, RenderVertex, Float3, Float4

SCALING_FACTOR = 1.52/20


class Material(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('diffuse', Float4),
        ('specular', Float3),
        ('specularity', ctypes.c_float),
        ('ambient', Float3),
        ('flag', ctypes.c_uint8),
        ('edge_color', Float4),
        ('edge_size', ctypes.c_float),
    ]


BONE_HAS_TAIL = 0x0001
BONE_HAS_IK = 0x0020
BONE_ROTATION_CONSTRAINT = 0x0100
BONE_TRANSLATION_CONSTRAINT = 0x0200
BONE_ROLL_AXIS = 0x0400
BONE_LOCAL_AXIS = 0x0800
BONE_EXTERNAL_PARENT = 0x2000


class Bone:
    def __init__(self, name_ja: str, name_en: str, position: Float3, parent_index: int) -> None:
        self.name_ja = name_ja
        self.name_en = name_en
        self.position = position
        self.parent_index = parent_index
        self.tail_position: Optional[Float3] = None


class Submesh:
    def __init__(self, name_ja: str, name_en: str, draw_count: int) -> None:
        self.name_ja = name_ja
        self.name_en = name_en
        self.draw_count = draw_count


class Pmx:
    def __init__(self, data: bytes) -> None:
        r = BytesReader(data)

        assert r.bytes(4) == b'PMX '
        assert r.float32() in (2.0, 2.1)
        assert r.uint8() == 8
        header = r.bytes(8)

        if header[0] == 0:
            encoding = 'utf16'
        elif header[1] == 1:
            encoding = 'utf8'

        def text_buf():
            n = r.uint32()
            return r.str(n, encoding)

        # additional uv
        assert header[1] == 0

        match header[2]:
            case 1:
                index_type = ctypes.c_uint8
            case 2:
                index_type = ctypes.c_uint16
            case 4:
                index_type = ctypes.c_uint32
            case _:
                raise NotImplementedError()

        def create_index_reader(size: int):
            match size:
                case 1:
                    def index_reader():
                        value = r.uint8()
                        if value == 255:
                            return -1
                        return value
                case 2:
                    def index_reader():
                        value = r.uint16()
                        if value == 65535:
                            return -1
                        return value

                case 4:
                    def index_reader():
                        return r.int32()
                case _:
                    raise NotImplementedError()
            return index_reader

        # texture_index
        texture_index = create_index_reader(header[3])

        # bone_index
        bone_index = create_index_reader(header[5])

        # info
        self.name_ja = text_buf()
        self.name_en = text_buf()
        self.comment_ja = text_buf()
        self.comment_en = text_buf()

        # vertices
        vertex_count = r.uint32()
        self.deform_bones: Dict[int, int] = {}
        self.vertices = (Vertex4BoneWeights * vertex_count)()
        for i, v in enumerate(self.vertices):
            rv = r.struct(RenderVertex)
            v.position = rv.position * SCALING_FACTOR
            v.normal = rv.normal
            v.uv = rv.uv

            flag = r.uint8()
            match flag:
                case 0:
                    # BDEF1
                    v.bone.x = bone_index()
                    v.bone.y = -1
                    v.bone.z = -1
                    v.bone.w = -1
                    v.weight.x = 1
                    v.weight.y = 0
                    v.weight.z = 0
                    v.weight.w = 0

                case 1:
                    # BDEF2
                    v.bone.x = bone_index()
                    v.bone.y = bone_index()
                    v.bone.z = -1
                    v.bone.w = -1
                    v.weight.x = r.float32()
                    v.weight.y = 1-v.weight.x
                    v.weight.z = 0
                    v.weight.w = 0

                case 2:
                    # BDEF4
                    v.bone.x = bone_index()
                    v.bone.y = bone_index()
                    v.bone.z = bone_index()
                    v.bone.w = bone_index()
                    v.weight.x = r.float32()
                    v.weight.y = r.float32()
                    v.weight.z = r.float32()
                    v.weight.w = r.float32()

                case 3:
                    # SDEF
                    b0 = bone_index()
                    b1 = bone_index()
                    w0 = r.float32()
                    c = r.struct(Float3)
                    r0 = r.struct(Float3)
                    r1 = r.struct(Float3)

                    # fall back to BDEF2
                    v.bone.x = b0
                    v.bone.y = b1
                    v.bone.z = -1
                    v.bone.w = -1
                    v.weight.x = w0
                    v.weight.y = 1-w0
                    v.weight.z = 0
                    v.weight.w = 0

            self.deform_bones[v.bone.x] = self.deform_bones.get(
                v.bone.x, 0) + 1
            self.deform_bones[v.bone.y] = self.deform_bones.get(
                v.bone.y, 0) + 1
            self.deform_bones[v.bone.z] = self.deform_bones.get(
                v.bone.z, 0) + 1
            self.deform_bones[v.bone.w] = self.deform_bones.get(
                v.bone.w, 0) + 1

            edge_scale = r.float32()

        # indices
        index_count = r.uint32()
        self.indices = r.array(index_type * index_count)

        # textures
        texture_count = r.uint32()
        for i in range(texture_count):
            text_buf()

        # materials
        self.submeshes: List[Submesh] = []
        material_count = r.uint32()
        for i in range(material_count):
            material_name_ja = text_buf()
            material_name_en = text_buf()
            material = r.struct(Material)
            texture = texture_index()
            sphere_texture = texture_index()
            sphere_mode = r.uint8()
            toon_flag = r.uint8()
            if toon_flag == 0:
                toon_index = texture_index()
            elif toon_flag == 1:
                toon_index = r.uint8()
            comment = text_buf()
            draw_count = r.uint32()
            self.submeshes.append(Submesh(material_name_ja, material_name_en, draw_count))

        # bones
        self.bones: List[Bone] = []
        bone_count = r.uint32()
        for i in range(bone_count):
            bone_name_ja = text_buf()
            bone_name_en = text_buf()
            position = r.struct(Float3)
            assert isinstance(position, Float3)
            parent_bone_index = bone_index()

            bone = Bone(bone_name_ja, bone_name_en,
                        position * SCALING_FACTOR, parent_bone_index)
            self.bones.append(bone)

            transform_layer = r.uint32()
            flags = r.uint16()

            if flags & BONE_HAS_TAIL:
                tail_index = bone_index()
            else:
                bone.tail_position = r.struct(
                    Float3) * SCALING_FACTOR  # type: ignore

            if flags & BONE_ROTATION_CONSTRAINT or flags & BONE_TRANSLATION_CONSTRAINT:
                source_index = bone_index()
                value = r.float32()

            if flags & BONE_ROLL_AXIS:
                axis = r.struct(Float3)

            if flags & BONE_LOCAL_AXIS:
                axis_x = r.struct(Float3)
                axis_z = r.struct(Float3)

            if flags & BONE_EXTERNAL_PARENT:
                key = r.uint32()

            if flags & BONE_HAS_IK:
                effector_index = bone_index()
                loop_count = r.uint32()
                rotation_limit = r.float32()
                chain_length = r.uint32()
                for j in range(chain_length):
                    joint_index = bone_index()
                    joint_rotation_limit = r.uint8()
                    if joint_rotation_limit:
                        min_limit = r.struct(Float3)
                        max_limit = r.struct(Float3)

    def __str__(self) -> str:
        return f'<pmx {self.name_ja}: {len(self.vertices)}vert, {len(self.indices)//3}tri, {len(self.bones)}bones>'

    def get_info(self) -> Iterable[str]:
        yield 'left-handed, A-stance'
        yield 'world-axis, inverted-pelvis'
        yield 'unit: 20/1.52'
