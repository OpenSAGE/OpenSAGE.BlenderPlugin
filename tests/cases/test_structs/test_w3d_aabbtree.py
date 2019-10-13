# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_aabbtree import AABBTree, AABBTreeHeader, AABBTreeNode, W3D_CHUNK_AABBTREE
from io_mesh_w3d.io_binary import read_chunk_head
from tests.helpers.w3d_aabbtree import get_aabbtree, compare_aabbtrees


class TestAABBTree(unittest.TestCase):
    def test_write_read(self):
        expected = get_aabbtree()

        self.assertEqual(8, expected.header.size_in_bytes())
        self.assertEqual(1252, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_AABBTREE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = AABBTree.read(self, io_stream, chunkEnd)
        compare_aabbtrees(self, expected, actual)


    def test_write_read_minimal(self):
        expected = get_aabbtree(num_nodes=0, num_polys=0)

        self.assertEqual(8, expected.header.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_AABBTREE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = AABBTree.read(self, io_stream, chunkEnd)
        compare_aabbtrees(self, expected, actual)

