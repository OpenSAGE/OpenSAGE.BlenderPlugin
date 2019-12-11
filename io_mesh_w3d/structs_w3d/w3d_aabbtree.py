# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector

from io_mesh_w3d.structs_w3d.w3d_struct import Struct, HEAD
from io_mesh_w3d.import_utils_w3d import skip_unknown_chunk
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.utils import *


W3D_CHUNK_AABBTREE_HEADER = 0x00000091


class AABBTreeHeader(Struct):
    node_count = 0
    poly_count = 0  # num tris of mesh

    @staticmethod
    def read(io_stream):
        result = AABBTreeHeader(
            node_count=read_ulong(io_stream),
            poly_count=read_ulong(io_stream))

        io_stream.read(24)  # padding
        return result

    @staticmethod
    def size(include_head=True):
        return const_size(8, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_AABBTREE_HEADER, io_stream,
                         self.size(False))
        write_ulong(self.node_count, io_stream)
        write_ulong(self.poly_count, io_stream)

        for pad in range(24):
            write_ubyte(0, io_stream)  # padding


class AABBTreeNode(Struct):
    min = Vector((0.0, 0.0, 0.0))
    max = Vector((0.0, 0.0, 0.0))
    front_or_poly_0 = 0
    back_or_poly_count = 0

    @staticmethod
    def read(io_stream):
        return AABBTreeNode(
            min=read_vector(io_stream),
            max=read_vector(io_stream),
            front_or_poly_0=read_long(io_stream),
            back_or_poly_count=read_long(io_stream))

    @staticmethod
    def size():
        return 32

    def write(self, io_stream):
        write_vector(self.min, io_stream)
        write_vector(self.max, io_stream)
        write_long(self.front_or_poly_0, io_stream)
        write_long(self.back_or_poly_count, io_stream)


W3D_CHUNK_AABBTREE = 0x00000090
W3D_CHUNK_AABBTREE_POLYINDICES = 0x00000092
W3D_CHUNK_AABBTREE_NODES = 0x00000093


class AABBTree(Struct):
    header = AABBTreeHeader()
    poly_indices = []
    nodes = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = AABBTree()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_AABBTREE_HEADER:
                result.header = AABBTreeHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_AABBTREE_POLYINDICES:
                result.poly_indices = read_list(
                    io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_AABBTREE_NODES:
                result.nodes = read_list(
                    io_stream, subchunk_end, AABBTreeNode.read)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        size += long_list_size(self.poly_indices)
        size += list_size(self.nodes)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_AABBTREE, io_stream,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)

        if self.poly_indices:
            write_chunk_head(W3D_CHUNK_AABBTREE_POLYINDICES, io_stream,
                             long_list_size(self.poly_indices, False))
            write_list(self.poly_indices, io_stream, write_long)
        if self.nodes:
            write_chunk_head(
                W3D_CHUNK_AABBTREE_NODES, io_stream, list_size(self.nodes, False))
            write_list(self.nodes, io_stream, AABBTreeNode.write)
