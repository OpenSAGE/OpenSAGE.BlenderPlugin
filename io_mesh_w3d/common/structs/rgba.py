# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3x.io_xml import *


class RGBA:
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

    @staticmethod
    def parse(xml_color):
        return RGBA(r=int(parse_float(xml_color, 'R', 0.0) * 255),
                    g=int(parse_float(xml_color, 'G', 0.0) * 255),
                    b=int(parse_float(xml_color, 'B', 0.0) * 255),
                    a=int(parse_float(xml_color, 'A', 0.0) * 255))

    @staticmethod
    def size():
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

    def create(self, parent):
        color = create_node(parent, 'C')
        color.set('R', format(self.r / 255))
        color.set('G', format(self.g / 255))
        color.set('B', format(self.b / 255))
        color.set('A', format(self.a / 255))

    def to_vector_rgba(self, scale=255.0):
        return self.r / scale, self.g / scale, self.b / scale, self.a / scale

    def to_vector_rgb(self, scale=255.0):
        return self.r / scale, self.g / scale, self.b / scale

    def __eq__(self, other):
        if isinstance(other, RGBA):
            return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a
        return False

    def __str__(self):
        return 'RGBA(r:' + str(self.r) + ', g:' + str(self.g) + \
               ', b:' + str(self.b) + ', a:' + str(self.a) + ')'
