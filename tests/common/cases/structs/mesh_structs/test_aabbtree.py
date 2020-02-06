# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.mesh_structs.aabbtree import *
from tests.utils import TestCase


class TestAABBTree(TestCase):
    def test_write_read(self):
        expected = get_aabbtree()

        self.assertEqual(16, expected.header.size())
        self.assertEqual(1260, expected.size())

        self.write_read_test(expected, W3D_CHUNK_AABBTREE, AABBTree.read, compare_aabbtrees, self, True, include_head=False)

    def test_write_read_empty(self):
        expected = get_aabbtree_empty()

        self.assertEqual(16, expected.header.size())

        self.write_read_test(expected, W3D_CHUNK_AABBTREE, AABBTree.read, compare_aabbtrees, self, True, include_head=False)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_AABBTREE, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_AABBTREE, chunk_type)

        AABBTree.read(self, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        expected = get_aabbtree_minimal()

        self.assertEqual(8, expected.header.size(False))
        self.assertEqual(16, expected.header.size())

        self.assertEqual(4, long_list_size(expected.poly_indices, False))

        self.assertEqual(32, list_size(expected.nodes, False))

        self.assertEqual(68, expected.size(False))
        self.assertEqual(76, expected.size())

    def test_write_read_xml(self):
        self.write_read_xml_test(get_aabbtree(xml=True), 'AABTree', AABBTree.parse, compare_aabbtrees)

    def test_write_read_minimal_xml(self):
        self.write_read_xml_test(get_aabbtree_minimal(), 'AABTree', AABBTree.parse, compare_aabbtrees)
