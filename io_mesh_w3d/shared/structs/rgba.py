# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *


class RGBA(Struct):
    r = 0
    g = 0
    b = 0
    a = 0

    def __init__(self, vec=None, a=None, scale=255, r=0, g=0, b=0):
        if vec is None:
            self.r = r
            self.g = g
            self.b = b
            if a is not None:
                self.a = int(a)
            else:
                self.a = 0
            return

        self.r = int(vec[0] * scale)
        self.g = int(vec[1] * scale)
        self.b = int(vec[2] * scale)
        if a is not None:
            self.a = int(a)
        else:
            self.a = int(vec[3] * scale)

    def is_black(self):
        return self.r == 0 and self.g == 0 and self.b == 0

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

    def to_vector_rgba(self, alpha=None, scale=255.0):
        if alpha is None:
            alpha = self.a / scale
        return (self.r / scale, self.g / scale, self.b / scale, alpha)

    def to_vector_rgb(self, scale=255.0):
        return (self.r / scale, self.g / scale, self.b / scale)

    def __eq__(self, other):
        if isinstance(other, RGBA):
            return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a
        return False

    def __str__(self):
        return 'RGBA(r:' + str(self.r) + ', g:' + str(self.g) + \
               ', b:' + str(self.b) + ', a:' + str(self.a) + ')'
