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
        return RGBA(r=read_float(io_stream),
                    g=read_float(io_stream),
                    b=read_float(io_stream),
                    a=read_float(io_stream))

    def write(self, io_stream):
        write_ubyte(io_stream, self.r)
        write_ubyte(io_stream, self.g)
        write_ubyte(io_stream, self.b)
        write_ubyte(io_stream, self.a)

    def write_f(self, io_stream):
        write_float(io_stream, self.r)
        write_float(io_stream, self.g)
        write_float(io_stream, self.b)
        write_float(io_stream, self.a)
