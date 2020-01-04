# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.utils import *
from io_mesh_w3d.w3d.structs.version import Version


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
        return const_size(40, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_HEADER, io_stream,
                         self.size(False))
        self.version.write(io_stream)
        write_ulong(self.lod_count, io_stream)
        write_fixed_string(self.model_name, io_stream)
        write_fixed_string(self.hierarchy_name, io_stream)


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
        return const_size(8, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER, io_stream,
                         self.size(False))
        write_ulong(self.model_count, io_stream)
        write_float(self.max_screen_size, io_stream)


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    bone_index = 0
    name_ = ""

    def name(self):
        if '.' in self.name_:
            return self.name_.split('.')[1]
        return self.name_

    @staticmethod
    def read(io_stream):
        return HLodSubObject(
            bone_index=read_ulong(io_stream),
            name_=read_long_fixed_string(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(36, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_SUB_OBJECT, io_stream,
                         self.size(False))
        write_ulong(self.bone_index, io_stream)
        write_long_fixed_string(self.name_, io_stream)


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
        size = const_size(0, include_head)
        size += self.header.size()
        size += list_size(self.sub_objects, False)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_LOD_ARRAY, io_stream,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        write_list(self.sub_objects, io_stream, HLodSubObject.write)


W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = HLodHeader()
    lod_arrays = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = HLod(
            header=None,
            lod_arrays=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_HEADER:
                result.header = HLodHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_LOD_ARRAY:
                result.lod_arrays.append(HLodArray.read(
                    context, io_stream, subchunk_end))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self):
        size = 0
        size += self.header.size()
        for lod_array in self.lod_arrays:
            size += lod_array.size()
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD, io_stream,
                         self.size(), has_sub_chunks=True)
        self.header.write(io_stream)
        for lod_array in self.lod_arrays:
            lod_array.write(io_stream)
