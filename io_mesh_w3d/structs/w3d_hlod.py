# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 11.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.import_utils_w3d import skip_unknown_chunk


W3D_CHUNK_HLOD_HEADER = 0x00000701


class HLodHeader(Struct):
    version = Version()
    lod_count = 1
    model_name = ""
    hierarchy_name = ""

    @staticmethod
    def read(io_stream):
        return HLodHeader(
            version=Version.read(io_stream),
            lod_count=read_ulong(io_stream),
            model_name=read_fixed_string(io_stream),
            hierarchy_name=read_fixed_string(io_stream))

    @staticmethod
    def size(include_head=True):
        size = 40
        if include_head:
            size += HEAD
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_HEADER,
                         self.size(False))
        self.version.write(io_stream)
        write_ulong(io_stream, self.lod_count)
        write_fixed_string(io_stream, self.model_name)
        write_fixed_string(io_stream, self.hierarchy_name)


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703


class HLodArrayHeader(Struct):
    model_count = 0
    max_screen_size = 0.0

    @staticmethod
    def read(io_stream):
        return HLodArrayHeader(
            model_count=read_ulong(io_stream),
            max_screen_size=read_float(io_stream))

    @staticmethod
    def size(include_head=True):
        size = 8
        if include_head:
            size += HEAD
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER,
                         self.size(False))
        write_ulong(io_stream, self.model_count)
        write_float(io_stream, self.max_screen_size)


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    bone_index = 0
    name = ""

    @staticmethod
    def read(io_stream):
        return HLodSubObject(
            bone_index=read_ulong(io_stream),
            name=read_long_fixed_string(io_stream))

    @staticmethod
    def size(include_head=True):
        size = 36
        if include_head:
            size += HEAD
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_SUB_OBJECT,
                         self.size(False))
        write_ulong(io_stream, self.bone_index)
        write_long_fixed_string(io_stream, self.name)


W3D_CHUNK_HLOD_LOD_ARRAY = 0x00000702


class HLodArray(Struct):
    header = HLodArrayHeader()
    sub_objects = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = HLodArray(
            header=None,
            sub_objects=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER:
                result.header = HLodArrayHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT:
                result.sub_objects.append(HLodSubObject.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = 0
        if include_head:
            size += HEAD
        size += self.header.size()
        for obj in self.sub_objects:
            size += obj.size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_LOD_ARRAY,
                         self.size(), has_sub_chunks=True)
        self.header.write(io_stream)
        for obj in self.sub_objects:
            obj.write(io_stream)


W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = HLodHeader()
    lod_array = HLodArray()

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = HLod(
            header=None,
            lod_array=None
        )

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_HEADER:
                result.header = HLodHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_LOD_ARRAY:
                result.lod_array = HLodArray.read(
                    context, io_stream, subchunk_end)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = 0
        if include_head:
            size += HEAD
        size += self.header.size()
        size += self.lod_array.size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        self.lod_array.write(io_stream)
