# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.structs_w3d.w3d_version import Version
from io_mesh_w3d.io_binary import *


class Triangle(Struct):
    vert_ids = (0, 0, 0)
    surface_type = 13
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0

    @staticmethod
    def read(io_stream):
        return Triangle(
            vert_ids=(read_ulong(io_stream), read_ulong(
                io_stream), read_ulong(io_stream)),
            surface_type=read_ulong(io_stream),
            normal=read_vector(io_stream),
            distance=read_float(io_stream))

    @staticmethod
    def size():
        return 32

    def write(self, io_stream):
        write_ulong(self.vert_ids[0], io_stream)
        write_ulong(self.vert_ids[1], io_stream)
        write_ulong(self.vert_ids[2], io_stream)
        write_ulong(self.surface_type, io_stream)
        write_vector(self.normal, io_stream)
        write_float(self.distance, io_stream)
