# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.utils.helpers import *

W3D_CHUNK_DAZZLE = 0x00000900
W3D_CHUNK_DAZZLE_NAME = 0x00000901
W3D_CHUNK_DAZZLE_TYPENAME = 0x00000902

# The dazzle is always assumed to be at the pivot point
# of the bone it is attached to (you should enable Export_Transform) for
# dazzles. If the dazzle-type (from dazzle.ini) is directional, then the
# coordinate-system of the bone will define the direction.


class Dazzle:
    def __init__(self, name_='', type_name=''):
        self.name_ = name_
        self.type_name = type_name

    def name(self):
        return self.name_.split('.')[-1]

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Dazzle(name_='', type_name='')

        while io_stream.tell() < chunk_end:
            chunk_type, chunk_size, _ = read_chunk_head(io_stream)
            if chunk_type == W3D_CHUNK_DAZZLE_NAME:
                result.name_ = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_DAZZLE_TYPENAME:
                result.type_name = read_string(io_stream)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += text_size(self.name_)
        size += text_size(self.type_name)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_DAZZLE, io_stream, self.size(False))

        write_chunk_head(W3D_CHUNK_DAZZLE_NAME, io_stream, text_size(self.name_, False))
        write_string(self.name_, io_stream)

        write_chunk_head(W3D_CHUNK_DAZZLE_TYPENAME, io_stream, text_size(self.type_name, False))
        write_string(self.type_name, io_stream)
