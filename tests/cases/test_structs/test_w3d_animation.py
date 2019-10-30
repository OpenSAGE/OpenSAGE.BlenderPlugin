# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_animation import Animation, W3D_CHUNK_ANIMATION
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_animation import get_animation, compare_animations


class TestAnimation(unittest.TestCase):
    def test_write_read(self):
        expected = get_animation()

        self.assertEqual(44, expected.header.size_in_bytes())
        self.assertEqual(2004, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = Animation.read(self, io_stream, chunkEnd)
        compare_animations(self, expected, actual)
