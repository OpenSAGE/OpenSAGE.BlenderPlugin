# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.io_binary import *

W3D_CHUNK_SHADERS = 0x00000029


class Shader:
    def __init__(self, depth_compare=0, depth_mask=0, color_mask=0, dest_blend=0, fog_func=0, pri_gradient=0,
                 sec_gradient=0, src_blend=0, texturing=0, detail_color_func=0, detail_alpha_func=0, shader_preset=0,
                 alpha_test=0, post_detail_color_func=0, post_detail_alpha_func=0, pad=0):
        self.depth_compare = depth_compare
        self.depth_mask = depth_mask
        self.color_mask = color_mask
        self.dest_blend = dest_blend
        self.fog_func = fog_func
        self.pri_gradient = pri_gradient
        self.sec_gradient = sec_gradient
        self.src_blend = src_blend
        self.texturing = texturing
        self.detail_color_func = detail_color_func
        self.detail_alpha_func = detail_alpha_func
        self.shader_preset = shader_preset
        self.alpha_test = alpha_test
        self.post_detail_color_func = post_detail_color_func
        self.post_detail_alpha_func = post_detail_alpha_func
        self.pad = pad

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
    def size():
        return 16

    def write(self, io_stream):
        write_ubyte(self.depth_compare, io_stream)
        write_ubyte(self.depth_mask, io_stream)
        write_ubyte(self.color_mask, io_stream)
        write_ubyte(self.dest_blend, io_stream)
        write_ubyte(self.fog_func, io_stream)
        write_ubyte(self.pri_gradient, io_stream)
        write_ubyte(self.sec_gradient, io_stream)
        write_ubyte(self.src_blend, io_stream)
        write_ubyte(self.texturing, io_stream)
        write_ubyte(self.detail_color_func, io_stream)
        write_ubyte(self.detail_alpha_func, io_stream)
        write_ubyte(self.shader_preset, io_stream)
        write_ubyte(self.alpha_test, io_stream)
        write_ubyte(self.post_detail_color_func, io_stream)
        write_ubyte(self.post_detail_alpha_func, io_stream)
        write_ubyte(self.pad, io_stream)
