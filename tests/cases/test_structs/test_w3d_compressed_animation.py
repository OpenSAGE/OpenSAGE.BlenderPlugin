# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 11.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_compressed_animation import *
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_compressed_animation import *


class TestCompressedAnimation(unittest.TestCase):
    def test_write_read(self):
        expected = get_compressed_animation()

        self.assertEqual(5940, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        compare_compressed_animations(self, expected, actual)

    def test_write_read_adaptive_delta(self):
        expected = get_compressed_animation(flavor=1)

        self.assertEqual(3631, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        compare_compressed_animations(self, expected, actual)

    def test_write_read_empty(self):
        expected = get_compressed_animation_empty()

        self.assertEqual(52, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        compare_compressed_animations(self, expected, actual)

    def test_chunk_sizes(self):
        ani = get_compressed_animation_minimal()

        self.assertEqual(44, ani.header.size(False))

        self.assertEqual(24, list_size(ani.time_coded_channels, False))
        self.assertEqual(34, list_size(ani.adaptive_delta_channels, False))
        self.assertEqual(20, list_size(ani.time_coded_bit_channels, False))
        self.assertEqual(24, list_size(ani.motion_channels, False))

        self.assertEqual(186, ani.size())