# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.structs_w3d.w3d_version import Version
from io_mesh_w3d.structs_w3d.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.utils import *

W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52


class ShaderMaterialHeader(Struct):
    number = 1  # what is this?
    type_name = ""
    reserved = 2  # what is this?

    @staticmethod
    def read(io_stream):
        return ShaderMaterialHeader(
            number=read_ubyte(io_stream),
            type_name=read_long_fixed_string(io_stream),
            reserved=read_long(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(37, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL_HEADER,
                         io_stream, self.size(False))
        write_ubyte(self.number, io_stream)
        write_long_fixed_string(self.type_name, io_stream)
        write_long(self.reserved, io_stream)


W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x53


class ShaderMaterialProperty(Struct):
    type = 0
    name = ""
    value = None

    @staticmethod
    def read(context, io_stream):
        type = read_long(io_stream)
        read_long(io_stream)  # num available chars
        name = read_string(io_stream)
        result = ShaderMaterialProperty(
            type=type,
            name=name)

        if result.type == 1:
            read_long(io_stream)  # num available chars
            result.value = read_string(io_stream)
        elif result.type == 2:
            result.value = read_float(io_stream)
        elif result.type == 3:
            result.value = read_vector2(io_stream)
        elif result.type == 4:
            result.value = read_vector(io_stream)
        elif result.type == 5:
            result.value = RGBA.read_f(io_stream)
        elif result.type == 6:
            result.value = read_long(io_stream)
        elif result.type == 7:
            result.value = read_ubyte(io_stream)
        else:
            message = "WARNING: unknown property type in shader material: %s" % result.type
            print(message)
            context.report({'ERROR'}, message)
        return result

    def size(self, include_head=True):
        size = const_size(8, include_head)
        size += len(self.name) + 1
        if self.type == 1:
            size += 4 + len(self.value) + 1
        elif self.type == 2:
            size += 4
        elif self.type == 3:
            size += 8
        elif self.type == 4:
            size += 12
        elif self.type == 5:
            size += 16
        elif self.type == 6:
            size += 4
        elif self.type == 7:
            size += 1
        else:
            message = "WARNING: invalid property type in shader material: %s" % self.type
            print(message)
        return size

    def write(self, io_stream):
        write_chunk_head(
            W3D_CHUNK_SHADER_MATERIAL_PROPERTY, io_stream,
            self.size(False))
        write_long(self.type, io_stream)
        write_long(len(self.name) + 1, io_stream)
        write_string(self.name, io_stream)

        if self.type == 1:
            write_long(len(self.value) + 1, io_stream)
            write_string(self.value, io_stream)
        elif self.type == 2:
            write_float(self.value, io_stream)
        elif self.type == 3:
            write_vector2(self.value, io_stream)
        elif self.type == 4:
            write_vector(self.value, io_stream)
        elif self.type == 5:
            self.value.write_f(io_stream)
        elif self.type == 6:
            write_long(self.value, io_stream)
        elif self.type == 7:
            write_ubyte(self.value, io_stream)
        else:
            message = "WARNING: invalid property type in shader material: %s" % self.type
            print(message)


W3D_CHUNK_SHADER_MATERIAL = 0x51


class ShaderMaterial(Struct):
    header = ShaderMaterialHeader()
    properties = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = ShaderMaterial(
            properties=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_SHADER_MATERIAL_HEADER:
                result.header = ShaderMaterialHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_PROPERTY:
                result.properties.append(
                    ShaderMaterialProperty.read(context, io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        for prop in self.properties:
            size += prop.size()
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL, io_stream,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        write_list(self.properties, io_stream,
                   ShaderMaterialProperty.write)
