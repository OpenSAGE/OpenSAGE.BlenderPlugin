# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.rgba import RGBA
from io_mesh_w3d.w3d.utils.helpers import *

W3D_CHUNK_VERTEX_MATERIALS = 0x0000002A
W3D_CHUNK_VERTEX_MATERIAL_INFO = 0x0000002D

USE_DEPTH_CUE = 0x1
ARGB_EMISSIVE_ONLY = 0x2
COPY_SPECULAR_TO_DIFFUSE = 0x4
DEPTH_CUE_TO_ALPHA = 0x8


class VertexMaterialInfo:
    def __init__(self, attributes=0, ambient=RGBA(), diffuse=RGBA(), specular=RGBA(), emissive=RGBA(), shininess=0.0,
                 opacity=1.0, translucency=0.0):
        self.attributes = attributes
        self.ambient = ambient  # alpha is only padding in this and below
        self.diffuse = diffuse
        self.specular = specular
        self.emissive = emissive
        self.shininess = shininess
        self.opacity = opacity
        self.translucency = translucency

    @staticmethod
    def read(io_stream):
        return VertexMaterialInfo(
            attributes=read_long(io_stream),
            ambient=RGBA.read(io_stream),
            diffuse=RGBA.read(io_stream),
            specular=RGBA.read(io_stream),
            emissive=RGBA.read(io_stream),
            shininess=read_float(io_stream),
            opacity=read_float(io_stream),
            translucency=read_float(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(32, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_VERTEX_MATERIAL_INFO, io_stream, self.size(False))
        write_long(self.attributes, io_stream)
        self.ambient.write(io_stream)
        self.diffuse.write(io_stream)
        self.specular.write(io_stream)
        self.emissive.write(io_stream)
        write_float(self.shininess, io_stream)
        write_float(self.opacity, io_stream)
        write_float(self.translucency, io_stream)


W3D_CHUNK_VERTEX_MATERIAL = 0x0000002B
W3D_CHUNK_VERTEX_MATERIAL_NAME = 0x0000002C
W3D_CHUNK_VERTEX_MAPPER_ARGS0 = 0x0000002E
W3D_CHUNK_VERTEX_MAPPER_ARGS1 = 0x0000002F


class VertexMaterial:
    def __init__(self, vm_name='', vm_info=None, vm_args_0='', vm_args_1=''):
        self.vm_name = vm_name
        self.vm_info = vm_info
        self.vm_args_0 = vm_args_0
        self.vm_args_1 = vm_args_1

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = VertexMaterial()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_VERTEX_MATERIAL_NAME:
                result.vm_name = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_MATERIAL_INFO:
                result.vm_info = VertexMaterialInfo.read(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_MAPPER_ARGS0:
                result.vm_args_0 = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_MAPPER_ARGS1:
                result.vm_args_1 = read_string(io_stream)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += text_size(self.vm_name)
        if self.vm_info is not None:
            size += self.vm_info.size()
        size += text_size(self.vm_args_0)
        size += text_size(self.vm_args_1)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_VERTEX_MATERIAL, io_stream, self.size(False), has_sub_chunks=True)
        write_chunk_head(W3D_CHUNK_VERTEX_MATERIAL_NAME, io_stream, text_size(self.vm_name, False))
        write_string(self.vm_name, io_stream)

        if self.vm_info is not None:
            self.vm_info.write(io_stream)

        if self.vm_args_0 is not '':
            write_chunk_head(W3D_CHUNK_VERTEX_MAPPER_ARGS0, io_stream, text_size(self.vm_args_0, False), io_stream)
            write_string(self.vm_args_0, io_stream)

        if self.vm_args_1 is not '':
            write_chunk_head(W3D_CHUNK_VERTEX_MAPPER_ARGS1, io_stream, text_size(self.vm_args_1, False))
            write_string(self.vm_args_1, io_stream)
