# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.shared.helpers.animation import *
from tests.utils import TestCase


class TestAnimation(TestCase):
    def test_write_read(self):
        expected = get_animation()

        self.assertEqual(52, expected.header.size())
        self.assertEqual(664, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_ANIMATION, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = Animation.read(self, io_stream, chunkEnd)
        compare_animations(self, expected, actual)

    def test_write_read_empty(self):
        expected = get_animation_empty()

        self.assertEqual(52, expected.header.size())
        self.assertEqual(52, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_ANIMATION, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = Animation.read(self, io_stream, chunkEnd)
        compare_animations(self, expected, actual)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_ANIMATION, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_ANIMATION, chunk_type)

        Animation.read(self, io_stream, subchunk_end)

    def test_validate(self):
        ani = get_animation()
        self.assertTrue(ani.validate(self))
        self.assertTrue(ani.validate(self, w3x=True))

        ani.header.name = 'tooooolonganiname'
        self.assertFalse(ani.validate(self))
        self.assertTrue(ani.validate(self, w3x=True))

        ani = get_animation()
        ani.header.hierarchy_name = 'tooooolonganiname'
        self.assertFalse(ani.validate(self))
        self.assertTrue(ani.validate(self, w3x=True))

        ani = get_animation()
        ani.channels = []
        self.assertFalse(ani.validate(self))
        self.assertFalse(ani.validate(self, w3x=True))

    def test_chunk_sizes(self):
        ani = get_animation_minimal()

        self.assertEqual(44, ani.header.size(False))

        self.assertEqual(43, list_size(ani.channels, False))

        self.assertEqual(95, ani.size())

    def test_write_read_xml(self):
        expected = get_animation(xml=True)

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_animations = dom.getElementsByTagName('W3DAnimation')
        self.assertEqual(1, len(xml_animations))

        actual = Animation.parse(xml_animations[0])
        compare_animations(self, expected, actual)

    def test_write_read_minimal_xml(self):
        expected = get_animation_minimal()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_animations = dom.getElementsByTagName('W3DAnimation')
        self.assertEqual(1, len(xml_animations))

        actual = Animation.parse(xml_animations[0])
        compare_animations(self, expected, actual)
