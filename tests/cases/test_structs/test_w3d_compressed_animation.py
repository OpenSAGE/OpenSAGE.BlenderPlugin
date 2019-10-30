# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_compressed_animation import CompressedAnimation, W3D_CHUNK_COMPRESSED_ANIMATION
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_compressed_animation import get_compressed_animation, compare_compressed_animations


class TestCompressedAnimation(unittest.TestCase):
    def test_write_read(self):
        expected = get_compressed_animation()

        self.assertEqual(5940, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        compare_compressed_animations(self, expected, actual)

    def test_write_read_adaptive_delta(self):
        expected = get_compressed_animation(_flavor=1)

        self.assertEqual(3631, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        compare_compressed_animations(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_compressed_animation(
            time_coded=False,
            bit_channels=False,
            motion_tc=False,
            motion_ad4=False,
            motion_ad8=False)

        self.assertEqual(52, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        compare_compressed_animations(self, expected, actual)
