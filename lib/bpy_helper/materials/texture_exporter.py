from typing import Optional
import os
import bpy
from ... import pyscene


def get_bytes(image: bpy.types.Image) -> Optional[pyscene.Texture]:
    '''
    io_scene_gltf2/blender/exp/gltf2_blender_image.py
    '''
    if image.source == 'FILE' and not image.is_dirty:
        data = None
        if image.packed_file is not None:
            data = image.packed_file.data
        else:
            src_path = bpy.path.abspath(image.filepath_raw)
            if os.path.isfile(src_path):
                with open(src_path, 'rb') as f:
                    data = f.read()
        # Check magic number is right
        if data:
            if data.startswith(b'\x89PNG'):
                return pyscene.Texture(image.name, data)
            if data.startswith(b'\xff\xd8\xff'):
                return pyscene.Texture(image.name, data)

    # Todo:
    # Copy to a temp image and save.
    tmp_image = None
    try:
        tmp_image = image.copy()
        tmp_image.update()

        if image.is_dirty:
            # Copy the pixels to get the changes
            tmp_buf = np.empty(image.size[0] * image.size[1] * 4, np.float32)
            image.pixels.foreach_get(tmp_buf)
            tmp_image.pixels.foreach_set(tmp_buf)
            tmp_buf = None  # GC this

        return _encode_temp_image(tmp_image, self.file_format)
    finally:
        if tmp_image is not None:
            bpy.data.images.remove(tmp_image, do_unlink=True)


def find_link(links: bpy.types.NodeLinks,
              socket: bpy.types.NodeSocket) -> Optional[bpy.types.NodeLink]:
    for l in links:
        if l.to_socket == socket:
            return l


def export_texture(tree: bpy.types.NodeTree,
                   socket: bpy.types.NodeSocket) -> Optional[pyscene.Texture]:

    l = find_link(tree.links, socket)
    if not l:
        return None

    if isinstance(l.from_node, bpy.types.ShaderNodeTexImage):
        return get_bytes(l.from_node.image)

    return None
