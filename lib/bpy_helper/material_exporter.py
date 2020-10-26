            # material
            # texture = None
            # if src.use_nodes:
            #     principled_bsdf = src.node_tree.nodes['Principled BSDF']
            #     if principled_bsdf:

            #         base_color = principled_bsdf.inputs["Base Color"]

            #         if base_color.is_linked:
            #             from_node = base_color.links[0].from_node
            #             if from_node.bl_idname == 'ShaderNodeTexImage':
            #                 image = from_node.image
            #                 if image:
            #                     color_texture_index = self.get_texture_index(
            #                         image, bufferManager)
            #                     color_texture = gltf.TextureInfo(
            #                         index=color_texture_index, texCoord=0)

            #         else:
            #             color = [x for x in base_color.default_value]

            # else:
            #     color = [x for x in src.diffuse_color]


            # texture
            # color_texture = src.texture
            # normal_texture = src.normal_map
            # alpha_mode = formats.gltf.MaterialAlphaMode.OPAQUE

            # if slot.use_map_color_diffuse and slot.texture and slot.texture.image:
            #     color_texture_index = self.get_texture_index(
            #         slot.texture.image, bufferManager)
            #     color_texture = gltf.TextureInfo(
            #         index=color_texture_index,
            #         texCoord=0
            #     )
            #     if slot.use_map_alpha:
            #         if slot.use_stencil:
            #             alpha_mode = gltf.AlphaMode.MASK
            #         else:
            #             alpha_mode = gltf.AlphaMode.BLEND
            # elif slot.use_map_normal and slot.texture and slot.texture.image:
            #     normal_texture_index = self.get_texture_index(
            #         slot.texture.image, bufferManager)
            #     normal_texture = gltf.MaterialNormalTextureInfo(
            #         index=normal_texture_index,
            #         texCoord=0,
            #         scale=slot.normal_factor,
            #     )


# def
    # '''
    # https://blender.stackexchange.com/questions/62072/does-blender-have-a-method-to-a-get-png-formatted-bytearray-for-an-image-via-pyt
    # '''
    # import struct
    # import zlib
    #
    # width = image.size[0]
    # height = image.size[1]
    # buf = bytes([int(p * 255) for p in image.pixels])  # type: ignore

    # # reverse the vertical line order and add null bytes at the start
    # width_byte_4 = width * 4
    # raw_data = b''.join(b'\x00' + buf[span:span + width_byte_4]
    #                     for span in range((height - 1) *
    #                                       width_byte_4, -1, -width_byte_4))

    # def png_pack(png_tag, data):
    #     chunk_head = png_tag + data
    #     return (struct.pack("!I", len(data)) + chunk_head +
    #             struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))

    # png_bytes = b''.join([
    #     b'\x89PNG\r\n\x1a\n',
    #     png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, 6, 0, 0, 0)),
    #     png_pack(b'IDAT', zlib.compress(raw_data, 9)),
    #     png_pack(b'IEND', b'')
    # ])
    # return png_bytes
