# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.io_binary import *


class RGBA(Struct):
    r = 0
    g = 0
    b = 0
    a = 0

    @staticmethod
    def read(io_stream):
        return RGBA(r=read_ubyte(io_stream),
                    g=read_ubyte(io_stream),
                    b=read_ubyte(io_stream),
                    a=read_ubyte(io_stream))

    @staticmethod
    def read_f(io_stream):
        return RGBA(r=int(read_float(io_stream) * 255),
                    g=int(read_float(io_stream) * 255),
                    b=int(read_float(io_stream) * 255),
                    a=int(read_float(io_stream) * 255))

    def size(self):
        return 4

    def write(self, io_stream):
        write_ubyte(self.r, io_stream)
        write_ubyte(self.g, io_stream)
        write_ubyte(self.b, io_stream)
        write_ubyte(self.a, io_stream)

    def write_f(self, io_stream):
        write_float(self.r / 255, io_stream)
        write_float(self.g / 255, io_stream)
        write_float(self.b / 255, io_stream)
        write_float(self.a / 255, io_stream)

    def __eq__(self, other):
        if isinstance(other, RGBA):
            return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a
        return False

    def __str__(self):
        return "RGBA(r:" + str(self.r) + ", g:" + str(self.g) + \
            ", b:" + str(self.b) + ", a:" + str(self.a) + ")"
