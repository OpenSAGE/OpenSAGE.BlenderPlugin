# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from io_mesh_w3d.structs.w3d_aabbtree import *
from io_mesh_w3d.io_binary import read_chunk_head
from tests.helpers.w3d_aabbtree import *


class TestAABBTree(unittest.TestCase):
    def test_write_read(self):
        expected = get_aabbtree()

        self.assertEqual(16, expected.header.size())
        self.assertEqual(1260, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_AABBTREE, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = AABBTree.read(self, io_stream, chunkEnd)
        compare_aabbtrees(self, expected, actual)

    def test_write_read_empty(self):
        expected = get_aabbtree_empty()

        self.assertEqual(16, expected.header.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_AABBTREE, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = AABBTree.read(self, io_stream, chunkEnd)
        compare_aabbtrees(self, expected, actual)

    def test_chunk_sizes(self):
        expected = get_aabbtree_minimal()

        self.assertEqual(8, expected.header.size(False))
        self.assertEqual(16, expected.header.size())

        self.assertEqual(4, long_list_size(expected.poly_indices, False))

        self.assertEqual(32, list_size(expected.nodes, False))

        self.assertEqual(68, expected.size(False))
        self.assertEqual(76, expected.size())
