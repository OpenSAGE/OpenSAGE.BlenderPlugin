# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.helpers.w3d_hierarchy import *


class TestHierarchy(TestCase):
    def test_write_read(self):
        expected = get_hierarchy()

        self.assertEqual(44, expected.header.size())
        self.assertEqual(636, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HIERARCHY, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = Hierarchy.read(self, io_stream, chunkEnd)
        compare_hierarchies(self, expected, actual)

    def test_write_read_empty(self):
        expected = get_hierarchy_empty()

        self.assertEqual(44, expected.header.size())
        self.assertEqual(44, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HIERARCHY, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = Hierarchy.read(self, io_stream, chunkEnd)
        compare_hierarchies(self, expected, actual)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_HIERARCHY, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_HIERARCHY, chunk_type)

        Hierarchy.read(self, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        hierarchy = get_hierarchy_minimal()

        self.assertEqual(36, hierarchy.header.size(False))
        self.assertEqual(44, hierarchy.header.size())

        self.assertEqual(60, list_size(hierarchy.pivots, False))

        self.assertEqual(12, vec_list_size(hierarchy.pivot_fixups, False))

        self.assertEqual(132, hierarchy.size())
