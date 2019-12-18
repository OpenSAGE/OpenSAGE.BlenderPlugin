# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
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
        write_chunk_head(W3D_CHUNK_MATERIAL_INFO, io_stream,
                         self.size(False))
        write_ulong(self.pass_count, io_stream)
        write_ulong(self.vert_matl_count, io_stream)
        write_ulong(self.shader_count, io_stream)
        write_ulong(self.texture_count, io_stream)
