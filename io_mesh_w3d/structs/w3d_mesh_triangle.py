# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from mathutils import Vector
from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.io_binary import *


class MeshTriangle(Struct):
    vert_ids = [0, 0, 0]
    surface_type = 13
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0

    @staticmethod
    def read(io_stream):
        return MeshTriangle(
            vert_ids=(read_ulong(io_stream), read_ulong(io_stream), read_ulong(io_stream)),
            surface_type=read_ulong(io_stream),
            normal=read_vector(io_stream),
            distance=read_float(io_stream))

    @staticmethod
    def size_in_bytes():
        return 32

    def write(self, io_stream):
        write_ulong(io_stream, self.vert_ids[0])
        write_ulong(io_stream, self.vert_ids[1])
        write_ulong(io_stream, self.vert_ids[2])
        write_ulong(io_stream, self.surface_type)
        write_vector(io_stream, self.normal)
        write_float(io_stream, self.distance)