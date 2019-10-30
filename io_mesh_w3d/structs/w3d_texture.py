# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.io_binary import *


W3D_CHUNK_TEXTURE_INFO = 0x00000033


class TextureInfo(Struct):
    attributes = 0
    animation_type = 0
    frame_count = 0
    frame_rate = 0.0

    @staticmethod
    def read(io_stream):
        return TextureInfo(
            attributes=read_ushort(io_stream),
            animation_type=read_ushort(io_stream),
            frame_count=read_ulong(io_stream),
            frame_rate=read_float(io_stream))

    @staticmethod
    def size_in_bytes(include_head=False):
        size = 12
        if include_head:
            size += HEAD
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_TEXTURE_INFO,
                         self.size_in_bytes())
        write_ushort(io_stream, self.attributes)
        write_ushort(io_stream, self.animation_type)
        write_ulong(io_stream, self.frame_count)
        write_float(io_stream, self.frame_rate)


W3D_CHUNK_TEXTURE = 0x00000031
W3D_CHUNK_TEXTURE_NAME = 0x00000032


class Texture(Struct):
    name = ""
    texture_info = None

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Texture(textureInfo=None)

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_TEXTURE_NAME:
                result.name = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_TEXTURE_INFO:
                result.texture_info = TextureInfo.read(io_stream)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self, include_head=False):
        size = 0
        if include_head:
            size += HEAD
        size += HEAD + len(self.name) + 1
        if self.texture_info is not None:
            size += self.texture_info.size_in_bytes(True)
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_TEXTURE,
                         self.size_in_bytes(), has_sub_chunks=True)
        write_chunk_head(io_stream, W3D_CHUNK_TEXTURE_NAME, len(self.name) + 1)
        write_string(io_stream, self.name)

        if self.texture_info is not None:
            self.texture_info.write(io_stream)
