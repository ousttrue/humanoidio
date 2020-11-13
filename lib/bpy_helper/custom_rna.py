'''
custom RNA property definitions
'''

import bpy

presets = (
    ('unknown', 'unknown', ''),
    ('neutral', 'neutral', ''),
    ('a', 'a', ''),
    ('i', 'i', ''),
    ('u', 'u', ''),
    ('e', 'e', ''),
    ('o', 'o', ''),
    ('blink', 'blink', ''),
    ('joy', 'joy', ''),
    ('angry', 'angry', ''),
    ('sorrow', 'sorrow', ''),
    ('fun', 'fun', ''),
    ('lookup', 'lookup', ''),
    ('lookdown', 'lookdown', ''),
    ('lookleft', 'lookleft', ''),
    ('lookright', 'lookright', ''),
    ('blink_l', 'blink_l', ''),
    ('blink_r', 'blink_r', ''),
)


class Expression(bpy.types.PropertyGroup):
    preset: bpy.props.EnumProperty(name="Expression preset",
                                   description="VRM Expression preset",
                                   items=presets)
    name: bpy.props.StringProperty(name="Preset", default="Unknown")
