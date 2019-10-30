# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_hierarchy import Hierarchy, HierarchyHeader, \
    HierarchyPivot, W3D_CHUNK_HIERARCHY
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_hierarchy import get_hierarchy, compare_hierarchies


class TestHierarchy(unittest.TestCase):
    def test_write_read(self):
        expected = get_hierarchy()

        self.assertEqual(36, expected.header.size_in_bytes())
        self.assertEqual(564, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HIERARCHY, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = Hierarchy.read(self, io_stream, chunkEnd)
        compare_hierarchies(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_hierarchy(minimal=True)

        self.assertEqual(36, expected.header.size_in_bytes())
        self.assertEqual(52, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HIERARCHY, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = Hierarchy.read(self, io_stream, chunkEnd)
        compare_hierarchies(self, expected, actual)
