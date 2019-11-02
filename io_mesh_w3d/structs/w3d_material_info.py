# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 11.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.utils import *


W3D_CHUNK_MATERIAL_INFO = 0x00000028


class MaterialInfo(Struct):
    pass_count = 0
    vert_matl_count = 0
    shader_count = 0
    texture_count = 0

    @staticmethod
    def read(io_stream):
        return MaterialInfo(
            pass_count=read_ulong(io_stream),
            vert_matl_count=read_ulong(io_stream),
            shader_count=read_ulong(io_stream),
            texture_count=read_ulong(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(16, include_head)

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_MATERIAL_INFO,
                             self.size(False))
        write_ulong(io_stream, self.pass_count)
        write_ulong(io_stream, self.vert_matl_count)
        write_ulong(io_stream, self.shader_count)
        write_ulong(io_stream, self.texture_count)
