# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_hierarchy import *
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_hierarchy import *


class TestHierarchy(unittest.TestCase):
    def test_write_read(self):
        expected = get_hierarchy()

        self.assertEqual(44, expected.header.size())
        self.assertEqual(564, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HIERARCHY, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = Hierarchy.read(self, io_stream, chunkEnd)
        compare_hierarchies(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_hierarchy_empty()

        self.assertEqual(44, expected.header.size())
        self.assertEqual(52, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HIERARCHY, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = Hierarchy.read(self, io_stream, chunkEnd)
        compare_hierarchies(self, expected, actual)

    def test_chunk_sizes(self):
        hierarchy = get_hierarchy_minimal()

        self.assertEqual(36, hierarchy.header.size(False))
        self.assertEqual(44, hierarchy.header.size())

        self.assertEqual(60, hierarchy.pivots_size(False))
        self.assertEqual(68, hierarchy.pivots_size())

        self.assertEqual(12, hierarchy.pivot_fixups_size(False))
        self.assertEqual(20, hierarchy.pivot_fixups_size())

        self.assertEqual(132, hierarchy.size())
