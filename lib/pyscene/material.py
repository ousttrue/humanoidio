from lib import pyscene
from logging import getLogger
logger = getLogger(__name__)
from typing import Optional, List, Dict, Union
import pathlib
from enum import Enum
#
import bpy
from ..formats import gltf
from ..formats.buffermanager import BufferManager
from ..struct_types import Float4


class TextureUsage(Enum):
    Unknown = 0
    Color = 1
    NormalMap = 2
    EmissiveTexture = 3
    OcclusionTexture = 4
    MetallicRoughnessTexture = 5


class Texture:
    def __init__(self, name: str, url_or_bytes: Union[pathlib.Path, bytes]):
        self.name = name
        self.url_or_bytes = url_or_bytes
        self.usage = TextureUsage.Unknown
        self.is_data = False

    def __str__(self) -> str:
        return f'<[{self.usage}] {self.name}>'

    def set_usage(self, usage: TextureUsage):
        if self.usage != TextureUsage.Unknown and self.usage != usage:
            raise Exception('multi use by different usage')
        self.usage = usage
        if usage in [
                TextureUsage.Color,
                TextureUsage.EmissiveTexture,
        ]:
            self.is_data = False
        else:
            self.is_data = True


class BlendMode(Enum):
    Opaque = 1
    AlphaBlend = 2
    Mask = 3


class Material:
    '''
    unlit
    '''
    def __init__(self, name: str):
        self.name = name
        self.color = Float4(1, 1, 1, 1)
        self.texture: Optional[Texture] = None
        self.blend_mode: BlendMode = BlendMode.Opaque
        self.threshold = 0.5
        self.double_sided = False

    def __str__(self):
        return f'<Unlit {self.name}>'

    def compare(self, other) -> bool:
        if self.__class__ != other.__class__:
            raise Exception(f'{self.__class__} != {other.__class__}')
        if self.name != other.name:
            raise Exception(f'{self.name} != {other.name}')

        if self.color != other.color:
            raise Exception('self.color != other.color')

        if not self._compare_texture(self.texture, other.texture):
            return False

        return True

    def _compare_texture(self, l: Optional[Texture],
                         r: Optional[Texture]):
        return True


class PBRMaterial(Material):
    '''
    PBR
    '''
    def __init__(self, name: str):
        super().__init__(name)
        self.metallic = 0.0
        self.roughness = 0.0  # 1 - smoothness
        self.normal_map: Optional[Texture] = None
        self.emissive_texture: Optional[Texture] = None
        self.metallic_roughness_texture: Optional[Texture] = None
        self.occlusion_texture: Optional[Texture] = None

    def __str__(self):
        return f'<PBR {self.name}>'

    def compare(self, other) -> bool:
        if not super().compare(other):
            return False

        return True
