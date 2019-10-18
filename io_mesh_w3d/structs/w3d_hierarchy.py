# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.import_utils_w3d import skip_unknown_chunk
from io_mesh_w3d.io_binary import *


W3D_CHUNK_HIERARCHY_HEADER = 0x00000101


class HierarchyHeader(Struct):
    version = Version()
    name = ""
    num_pivots = 0
    center_pos = Vector((0.0, 0.0, 0.0))

    @staticmethod
    def read(io_stream):
        return HierarchyHeader(
            version=Version.read(io_stream),
            name=read_fixed_string(io_stream),
            num_pivots=read_ulong(io_stream),
            center_pos=read_vector(io_stream))

    @staticmethod
    def size_in_bytes():
        return 36

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HIERARCHY_HEADER, self.size_in_bytes())
        self.version.write(io_stream)
        write_fixed_string(io_stream, self.name)
        write_ulong(io_stream, self.num_pivots)
        write_vector(io_stream, self.center_pos)


W3D_CHUNK_PIVOTS = 0x00000102


class HierarchyPivot(Struct):
    name = ""
    parent_id = -1
    translation = Vector((0.0, 0.0, 0.0))
    euler_angles = Vector((0.0, 0.0, 0.0))
    rotation = Quaternion((1.0, 0.0, 0.0, 0.0))

    @staticmethod
    def read(io_stream):
        return HierarchyPivot(
            name=read_fixed_string(io_stream),
            parent_id=read_long(io_stream),
            translation=read_vector(io_stream),
            euler_angles=read_vector(io_stream),
            rotation=read_quaternion(io_stream))

    @staticmethod
    def size_in_bytes():
        return 60

    def write(self, io_stream):
        write_fixed_string(io_stream, self.name)
        write_long(io_stream, self.parent_id)
        write_vector(io_stream, self.translation)
        write_vector(io_stream, self.euler_angles)
        write_quaternion(io_stream, self.rotation)


W3D_CHUNK_HIERARCHY = 0x00000100
W3D_CHUNK_PIVOT_FIXUPS = 0x00000103


class Hierarchy(Struct):
    header = HierarchyHeader()
    pivots = []
    pivot_fixups = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Hierarchy(
            pivots=[],
            pivot_fixups=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HIERARCHY_HEADER:
                result.header = HierarchyHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_PIVOTS:
                result.pivots = read_array(
                    io_stream, subchunk_end, HierarchyPivot.read)
            elif chunk_type == W3D_CHUNK_PIVOT_FIXUPS:
                result.pivot_fixups = read_array(
                    io_stream, subchunk_end, read_vector)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def pivots_size(self):
        size = 0
        for pivot in self.pivots:
            size += pivot.size_in_bytes()
        return size

    def pivot_fixups_size(self):
        size = 0
        for _ in self.pivot_fixups:
            size += 12  # size in bytes
        return size

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        size += HEAD + self.pivots_size()
        if self.pivot_fixups:
            size += HEAD + self.pivot_fixups_size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HIERARCHY, self.size_in_bytes())
        self.header.write(io_stream)
        write_chunk_head(io_stream, W3D_CHUNK_PIVOTS, self.pivots_size())
        for pivot in self.pivots:
            pivot.write(io_stream)

        if self.pivot_fixups:
            write_chunk_head(io_stream, W3D_CHUNK_PIVOT_FIXUPS,
                             self.pivot_fixups_size())
            for fixup in self.pivot_fixups:
                write_vector(io_stream, fixup)