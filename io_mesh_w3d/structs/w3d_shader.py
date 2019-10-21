# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.io_binary import *

class Shader(Struct):
    depth_compare = 0
    depth_mask = 0
    color_mask = 0
    dest_blend = 0
    fog_func = 0
    pri_gradient = 0
    sec_gradient = 0
    src_blend = 0
    texturing = 0
    detail_color_func = 0
    detail_alpha_func = 0
    shader_preset = 0
    alpha_test = 0
    post_detail_color_func = 0
    post_detail_alpha_func = 0
    pad = 0

    @staticmethod
    def read(io_stream):
        return Shader(
            depth_compare=read_ubyte(io_stream),
            depth_mask=read_ubyte(io_stream),
            color_mask=read_ubyte(io_stream),
            dest_blend=read_ubyte(io_stream),
            fog_func=read_ubyte(io_stream),
            pri_gradient=read_ubyte(io_stream),
            sec_gradient=read_ubyte(io_stream),
            src_blend=read_ubyte(io_stream),
            texturing=read_ubyte(io_stream),
            detail_color_func=read_ubyte(io_stream),
            detail_alpha_func=read_ubyte(io_stream),
            shader_preset=read_ubyte(io_stream),
            alpha_test=read_ubyte(io_stream),
            post_detail_color_func=read_ubyte(io_stream),
            post_detail_alpha_func=read_ubyte(io_stream),
            pad=read_ubyte(io_stream))

    @staticmethod
    def size_in_bytes():
        return 16

    def write(self, io_stream):
        write_ubyte(io_stream, self.depth_compare)
        write_ubyte(io_stream, self.depth_mask)
        write_ubyte(io_stream, self.color_mask)
        write_ubyte(io_stream, self.dest_blend)
        write_ubyte(io_stream, self.fog_func)
        write_ubyte(io_stream, self.pri_gradient)
        write_ubyte(io_stream, self.sec_gradient)
        write_ubyte(io_stream, self.src_blend)
        write_ubyte(io_stream, self.texturing)
        write_ubyte(io_stream, self.detail_color_func)
        write_ubyte(io_stream, self.detail_alpha_func)
        write_ubyte(io_stream, self.shader_preset)
        write_ubyte(io_stream, self.alpha_test)
        write_ubyte(io_stream, self.post_detail_color_func)
        write_ubyte(io_stream, self.post_detail_alpha_func)
        write_ubyte(io_stream, self.pad)
