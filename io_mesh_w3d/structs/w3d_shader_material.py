# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import *

W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52


class ShaderMaterialHeader(Struct):
    number = 0
    type_name = ""
    reserved = 0

    @staticmethod
    def read(io_stream):
        return ShaderMaterialHeader(
            number=read_ubyte(io_stream),
            type_name=read_long_fixed_string(io_stream),
            reserved=read_long(io_stream))

    @staticmethod
    def size_in_bytes():
        return 37

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_SHADER_MATERIAL_HEADER, self.size_in_bytes())
        write_ubyte(io_stream, self.number)
        write_long_fixed_string(io_stream, self.type_name)
        write_long(io_stream, self.reserved)


W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x53


class ShaderMaterialProperty(Struct):
    type = 0
    name = ""
    num_chars = 0
    value = None

    @staticmethod
    def read(io_stream):
        result = ShaderMaterialProperty(
            type=read_long(io_stream),
            num_chars=read_long(io_stream),
            name=read_string(io_stream))

        if result.type == 1:
            read_long(io_stream)  # num available chars
            result.value = read_string(io_stream)
        elif result.type == 2:
            result.value = read_float(io_stream)
        elif result.type == 4:
            result.value = read_vector(io_stream)
        elif result.type == 5:
            result.value = RGBA.read_f(io_stream)
        elif result.type == 6:
            result.value = read_long(io_stream)
        elif result.type == 7:
            result.value = read_ubyte(io_stream)
        return result

    def size_in_bytes(self):
        size = 8 + len(self.name) + 1
        if self.type == 1:
            size += 4 + len(self.value) + 1
        elif self.type == 2:
            size += 4
        elif self.type == 4:
            size += 12
        elif self.type == 5:
            size += 16
        elif self.type == 6:
            size += 4
        elif self.type == 7:
            size += 1
        return size

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_SHADER_MATERIAL_PROPERTY, self.size_in_bytes())
        write_long(io_stream, self.type)
        write_long(io_stream, self.num_chars)
        write_string(io_stream, self.name)

        if self.type == 1:
            write_long(io_stream, len(self.value) + 1)
            write_string(io_stream, self.value)
        elif self.type == 2:
            write_float(io_stream, self.value)
        elif self.type == 4:
            write_vector(io_stream, self.value)
        elif self.type == 5:
            self.value.write_f(io_stream)
        elif self.type == 6:
            write_long(io_stream, self.value)
        elif self.type == 7:
            write_ubyte(io_stream, self.value)


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
                result.properties.append(ShaderMaterialProperty.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for prop in self.properties:
            size += HEAD + prop.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_SHADER_MATERIAL,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)
        for prop in self.properties:
            prop.write(io_stream)
