# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from io_mesh_w3d.structs.w3d_animation import *
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_animation import *


class TestAnimation(unittest.TestCase):
    def test_write_read(self):
        expected = get_animation()

        self.assertEqual(52, expected.header.size())
        self.assertEqual(2004, expected.size())

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

    def test_chunk_sizes(self):
        ani = get_animation_minimal()

        self.assertEqual(44, ani.header.size(False))

        self.assertEqual(148, list_size(ani.channels, False))

        self.assertEqual(200, ani.size())
