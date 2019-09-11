# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_texture import Texture, TextureInfo, W3D_CHUNK_TEXTURE
from io_mesh_w3d.io_binary import read_chunk_head


class TestTexture(unittest.TestCase):
    def test_write_read(self):
        expected = Texture(
            name="TestName")

        expected.texture_info = TextureInfo(
            attributes=555,
            animation_type=33,
            frame_count=63,
            frame_rate=16.0)

        self.assertEqual(12, expected.texture_info.size_in_bytes())
        self.assertEqual(37, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = Texture.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.name, actual.name)

        self.assertEqual(expected.texture_info.attributes, actual.texture_info.attributes)
        self.assertEqual(expected.texture_info.animation_type, actual.texture_info.animation_type)
        self.assertEqual(expected.texture_info.frame_count, actual.texture_info.frame_count)
        self.assertEqual(expected.texture_info.frame_rate, actual.texture_info.frame_rate)
