from logging import getLogger
logger = getLogger(__name__)
from typing import Dict
import pathlib
import tempfile
import bpy
from .. import pyscene
from ..import_map import ImportMap


class TextureImporter:
    def __init__(self, import_map: ImportMap):
        self.import_map = import_map

    def get_or_create_image(self, texture: pyscene.Texture) -> bpy.types.Image:
        bl_image = self.import_map.image.get(texture)
        if bl_image:
            return bl_image

        logger.debug(f'create {texture}')

        if isinstance(texture.url_or_bytes, pathlib.Path):
            path = texture.url_or_bytes.absolute()
            bl_image = bpy.data.images.load(str(path))  # type: ignore

        elif isinstance(texture.url_or_bytes, bytes):
            # Image stored as data => create a tempfile, pack, and delete file
            # img_from_file = False
            img_data = texture.url_or_bytes
            # img_name = img_name or 'Image_%d' % img_idx
            tmp_dir = tempfile.TemporaryDirectory(prefix='gltfimg-')
            # filename = _filenamify(img_name) or 'Image_%d' % img_idx
            # filename += _img_extension(img)
            path = pathlib.Path(tmp_dir.name) / texture.name
            with open(path, 'wb') as f:
                f.write(img_data)
            bl_image = bpy.data.images.load(str(path))  # type: ignore
            bl_image.pack()

        else:
            raise Exception()

        bl_image.colorspace_settings.is_data = texture.is_data
        bl_image.name = texture.name

        self.import_map.image[texture] = bl_image
        return bl_image
