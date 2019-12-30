# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.utils import *

W3D_CHUNK_DAZZLE = 0x00000900
W3D_CHUNK_DAZZLE_NAME = 0x00000901
W3D_CHUNK_DAZZLE_TYPENAME = 0x00000902


class Dazzle(Struct):
    name = ""
    type_name = ""

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Dazzle(name="", type_name="")

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)
            if chunk_type == W3D_CHUNK_DAZZLE_NAME:
                result.name = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_DAZZLE_TYPENAME:
                result.type_name = read_string(io_stream)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += text_size(self.name)
        size += text_size(self.type_name)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_DAZZLE, io_stream, self.size(False))

        write_chunk_head(W3D_CHUNK_DAZZLE_NAME, io_stream, text_size(self.name, False))
        write_string(self.name, io_stream)

        write_chunk_head(W3D_CHUNK_DAZZLE_TYPENAME, io_stream, text_size(self.type_name, False))
        write_string(self.type_name, io_stream)
