# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import *


W3D_CHUNK_VERTEX_MATERIAL_INFO = 0x0000002D

USE_DEPTH_CUE = 0x1
ARGB_EMISSIVE_ONLY = 0x2
COPY_SPECULAR_TO_DIFFUSE = 0x4
DEPTH_CUE_TO_ALPHA = 0x8


class VertexMaterialInfo(Struct):
    attributes = 0
    ambient = RGBA()  # alpha is only padding in this and below
    diffuse = RGBA()
    specular = RGBA()
    emissive = RGBA()
    shininess = 0.0
    opacity = 0.0
    translucency = 0.0

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
        size = 32
        if include_head:
            size += HEAD
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIAL_INFO,
                         self.size(False))
        write_long(io_stream, self.attributes)
        self.ambient.write(io_stream)
        self.diffuse.write(io_stream)
        self.specular.write(io_stream)
        self.emissive.write(io_stream)
        write_float(io_stream, self.shininess)
        write_float(io_stream, self.opacity)
        write_float(io_stream, self.translucency)


W3D_CHUNK_VERTEX_MATERIAL = 0x0000002B
W3D_CHUNK_VERTEX_MATERIAL_NAME = 0x0000002C
W3D_CHUNK_VERTEX_MAPPER_ARGS0 = 0x0000002E
W3D_CHUNK_VERTEX_MAPPER_ARGS1 = 0x0000002F


class VertexMaterial(Struct):
    vm_name = ""
    vm_info = None
    vm_args_0 = ""
    vm_args_1 = ""

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

    @staticmethod
    def name_size(name, include_head=True):
        size = len(name) + 1
        if include_head:
            size += HEAD
        return size

    def size(self, include_head=True):
        size = 0
        if include_head:
            size += HEAD
        size += self.name_size(self.vm_name)
        if self.vm_info is not None:
            size += self.vm_info.size()
        if self.vm_args_0 is not "":
            size += self.name_size(self.vm_args_0)
        if self.vm_args_1 is not "":
            size += self.name_size(self.vm_args_1)
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIAL,
                         self.size(False), has_sub_chunks=True)
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIAL_NAME,
                         self.name_size(self.vm_name, False))
        write_string(io_stream, self.vm_name)

        if self.vm_info is not None:
            self.vm_info.write(io_stream)

        if self.vm_args_0 is not "":
            write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MAPPER_ARGS0,
                             self.name_size(self.vm_args_0, False))
            write_string(io_stream, self.vm_args_0)

        if self.vm_args_1 is not "":
            write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MAPPER_ARGS1,
                             self.name_size(self.vm_args_1, False))
            write_string(io_stream, self.vm_args_1)
