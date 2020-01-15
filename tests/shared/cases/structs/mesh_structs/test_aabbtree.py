# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.shared.helpers.mesh_structs.aabbtree import *
from tests.utils import TestCase


class TestAABBTree(TestCase):
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
        expected = get_aabbtree(xml=True)

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_aabbtrees = dom.getElementsByTagName('AABTree')
        self.assertEqual(1, len(xml_aabbtrees))

        actual = AABBTree.parse(xml_aabbtrees[0])
        compare_aabbtrees(self, expected, actual)

    def test_write_read_minimal_xml(self):
        expected = get_aabbtree_minimal()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_aabbtrees = dom.getElementsByTagName('AABTree')
        self.assertEqual(1, len(xml_aabbtrees))

        actual = AABBTree.parse(xml_aabbtrees[0])
        compare_aabbtrees(self, expected, actual)
