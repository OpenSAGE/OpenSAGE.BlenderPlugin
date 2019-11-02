# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

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
        write_ubyte(io_stream, self.r)
        write_ubyte(io_stream, self.g)
        write_ubyte(io_stream, self.b)
        write_ubyte(io_stream, self.a)

    def write_f(self, io_stream):
        write_float(io_stream, self.r / 255)
        write_float(io_stream, self.g / 255)
        write_float(io_stream, self.b / 255)
        write_float(io_stream, self.a / 255)

    def __eq__(self, other):
        if isinstance(other, RGBA):
            return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a
        return False

    def __str__(self):
        return "RGBA(r:" + str(self.r) + ", g:" + str(self.g) + \
            ", b:" + str(self.b) + ", a:" + str(self.a) + ")"
