# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from tests import utils

from io_mesh_w3d.structs.w3d_compressed_animation import *
from io_mesh_w3d.io_binary import *

from tests.helpers.w3d_compressed_animation import *


class TestCompressedAnimation(utils.W3dTestCase):
    def test_write_read(self):
        expected = get_compressed_animation()

        self.assertEqual(3740, expected.size())

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

    def test_unknown_chunk_skip(self):
        context = utils.ImportWrapper(self.outpath())
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_COMPRESSED_ANIMATION, output, 70, has_sub_chunks=True)

        header = get_compressed_animation_header(flavor=2)
        header.write(output)

        write_chunk_head(W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunk_type)

        CompressedAnimation.read(context, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        ani = get_compressed_animation_minimal()

        self.assertEqual(44, ani.header.size(False))

        self.assertEqual(24, list_size(ani.time_coded_channels, False))
        self.assertEqual(34, list_size(ani.adaptive_delta_channels, False))
        self.assertEqual(20, list_size(ani.time_coded_bit_channels, False))
        self.assertEqual(24, list_size(ani.motion_channels, False))

        self.assertEqual(154, ani.size())