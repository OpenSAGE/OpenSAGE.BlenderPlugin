# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from mathutils import Vector

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import *


W3D_CHUNK_BOX = 0x00000740


class Box(Struct):
    version = Version()
    box_type = 0
    collision_types = 0
    name = ""
    color = RGBA()
    center = Vector((0.0, 0.0, 0.0))
    extend = Vector((0.0, 0.0, 0.0))

    @staticmethod
    def read(io_stream):
        ver = Version.read(io_stream)
        flags = read_ulong(io_stream)
        return Box(
            version=ver,
            box_type=(flags & 0b11),
            collision_types=(flags & 0xFF0),
            name=read_long_fixed_string(io_stream),
            color=RGBA.read(io_stream),
            center=read_vector(io_stream),
            extend=read_vector(io_stream))

    @staticmethod
    def size_in_bytes():
        return 68

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_BOX, self.size_in_bytes())

        self.version.write(io_stream)
        write_ulong(io_stream, (self.collision_types & 0xFF)
                    | (self.box_type & 0b11))
        write_long_fixed_string(io_stream, self.name)
        self.color.write(io_stream)
        write_vector(io_stream, self.center)
        write_vector(io_stream, self.extend)
