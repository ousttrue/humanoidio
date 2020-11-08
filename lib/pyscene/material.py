from logging import getLogger
logger = getLogger(__name__)
from typing import Optional, List, Dict, Union, Tuple
import pathlib
from enum import Enum
#
import bpy
from ..struct_types import Float2, Float3, Float4


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
        self.scale = Float2(1, 1)
        self.translation = Float2(0, 0)

    def __str__(self) -> str:
        return f'<[{self.usage}] {self.name}>'

    def compare(self, other) -> bool:
        if self.name != other.name:
            raise Exception(f'{self.name} != {other.name}')
        if self.url_or_bytes != other.url_or_bytes:
            raise Exception(f'self.url_or_bytes != other.url_or_bytes')
        if self.usage != other.usage:
            raise Exception(f'{self.usage} != {other.usage}')
        return True

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


class CullMode(Enum):
    No = 1
    Back = 2
    Front = 3


def comapare_texture(msg: str, l, r) -> bool:
    if l and not r:
        raise Exception(f'other.{msg} is None')
    elif not l and r:
        raise Exception(f'self.{msg} is None')
    elif l and r:
        # if not self.color_texture.compare(other.color_texture):
        #     return False
        return True
    else:
        return True


class UnlitMaterial:
    '''
    Unlit

    Color
    Opaque/AlphaBlend/Mask
    Backface culling
    '''
    def __init__(self, name: str):
        self.name = name
        self.color = Float4(1, 1, 1, 1)
        self.color_texture: Optional[Texture] = None
        self.blend_mode: BlendMode = BlendMode.Opaque
        self.threshold = 0.5
        self.double_sided = False

    def __str__(self):
        return f'<Unlit {self.name}>'

    def compare(self, other: 'UnlitMaterial') -> bool:
        if self.__class__ != other.__class__:
            raise Exception(f'{self.__class__} != {other.__class__}')
        if self.name != other.name:
            raise Exception(f'{self.name} != {other.name}')

        if self.color != other.color:
            raise Exception('self.color != other.color')

        if not comapare_texture('color_texture', self.color_texture,
                            other.color_texture):
            return False

        return True


class PBRMaterial(UnlitMaterial):
    '''
    PhysicallyBasedRendering Material

    BaseColor
    Emission
    MetallicRoughness
    NormalMap

    etc...
    '''
    def __init__(self, name: str):
        super().__init__(name)
        self.metallic = 1
        self.roughness = 1  # 1 - smoothness
        self.normal_texture: Optional[Texture] = None
        self.normal_scale = 1.0
        self.emissive_texture: Optional[Texture] = None
        self.emissive_color = Float3(0, 0, 0)
        self.metallic_roughness_texture: Optional[Texture] = None
        self.occlusion_texture: Optional[Texture] = None
        self.occlusion_strength = 1.0

    def __str__(self):
        return f'<PBR {self.name}>'

    def compare(self, other) -> bool:
        if not super().compare(other):
            return False

        return True


class MToonMaterial(UnlitMaterial):
    '''
    MToon
    '''
    def __init__(self, name: str):
        super().__init__(name)
        self.zwrite = True
        # normal
        self.normal_texture: Optional[Texture] = None
        self.normal_scale = 1.0
        # emissive
        self.emissive_texture: Optional[Texture] = None
        self.emissive_color = Float3(0, 0, 0)
        # toon
        self.shade_color = Float3(1, 1, 1)
        self.shade_texture: Optional[Texture] = None
        self.shade_toony = 0.9
        self.shading_shift = 0
        # matcap
        self.matcap_texture: Optional[Texture] = None

    def set_scalar(self, k: str, v: float):
        if k == '_Cutoff':
            self.threshold = v
        elif k == '_BumpScale':
            self.normal_scale = v
        elif k == '_BlendMode':
            if v == 0:
                self.blend_mode = BlendMode.Opaque
            elif v == 1:
                self.blend_mode = BlendMode.Mask
            elif v == 2:
                self.blend_mode = BlendMode.AlphaBlend
            else:
                raise NotImplementedError()
        elif k == '_CullMode':
            if v == 0:
                self.double_sided = True
            elif v == 2:
                self.double_sided = False
            else:
                raise NotImplementedError()
        elif k == '_ZWrite':
            if v == 1:
                self.zwrite = True
            elif v == 0:
                self.zwrite = False
            else:
                raise NotImplementedError()
        elif k == '_ShadeToony':
            self.shade_toony = v
        elif k == '_ShadeShift':
            self.shading_shift = v
        elif k in [
                # ToDo
                '_ReceiveShadowRate',
                '_ShadingGradeRate',
                '_LightColorAttenuation',
                '_IndirectLightIntensity',
                '_OutlineWidth',
                '_OutlineScaledMaxDistance',
                '_OutlineLightingMix',
                '_OutlineWidthMode',
                '_OutlineColorMode',
                '_OutlineCullMode',
                #
                '_SrcBlend',
                '_DstBlend',
                '_DebugMode',
        ]:
            pass
        else:
            raise KeyError(f'unknown {k}')

    def set_texture(self, k: str, texture: Texture):
        if k == '_MainTex':
            self.color_texture = texture
        elif k == '_BumpMap':
            texture.is_data = True
            self.normal_texture = texture
        elif k == '_EmissionMap':
            self.emissive_texture = texture
        elif k == '_SphereAdd':
            self.matcap_texture = texture
        elif k == '_ShadeTexture':
            self.shade_texture = texture
        elif k in [
                # Todo
                '_ReceiveShadowTexture',
                '_ShadingGradeTexture',
                '_OutlineWidthTexture',
        ]:
            pass
        else:
            raise NotImplementedError()

    def set_vector4(self, k: str, v: List[float]):
        if k == '_Color':
            self.color.x = v[0]
            self.color.y = v[1]
            self.color.z = v[2]
            self.color.w = v[3]
        elif k == '_EmissionColor':
            self.emissive_color.x = v[0]
            self.emissive_color.y = v[1]
            self.emissive_color.z = v[2]
        elif k == '_OutlineColor':
            pass
        elif k == '_ShadeColor':
            self.shade_color.x = v[0]
            self.shade_color.y = v[1]
            self.shade_color.z = v[2]
        elif k in [
                # Todo
                '_MainTex',
                '_ShadeTexture',
                '_BumpMap',
                '_ReceiveShadowTexture',
                '_ShadingGradeTexture',
                '_SphereAdd',
                '_EmissionMap',
                '_OutlineWidthTexture',
        ]:
            pass
        else:
            raise KeyError(f'unknown {k}')
