# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.io_binary import *


class VertexInfluence(Struct):
    bone_idx = 0
    xtra_idx = 0
    bone_inf = 0.0
    xtra_inf = 0.0

    @staticmethod
    def read(io_stream):
        return VertexInfluence(
            bone_idx=read_ushort(io_stream),
            xtra_idx=read_ushort(io_stream),
            bone_inf=read_ushort(io_stream) / 100,
            xtra_inf=read_ushort(io_stream) / 100)

    @staticmethod
    def size():
        return 8

    def write(self, io_stream):
        write_ushort(io_stream, self.bone_idx)
        write_ushort(io_stream, self.xtra_idx)
        write_ushort(io_stream, int(self.bone_inf * 100))
        write_ushort(io_stream, int(self.xtra_inf * 100))
