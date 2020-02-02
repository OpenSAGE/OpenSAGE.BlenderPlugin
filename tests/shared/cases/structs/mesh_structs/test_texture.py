# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.shared.helpers.mesh_structs.texture import *
from tests.utils import TestCase


class TestTexture(TestCase):
    def test_write_read(self):
        expected = get_texture()

        self.assertEqual(20, expected.texture_info.size())
        self.assertEqual(48, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = Texture.read(self, io_stream, chunkEnd)
        compare_textures(self, expected, actual)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_TEXTURE, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_TEXTURE, chunk_type)

        Texture.read(self, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        tex = get_texture_minimal()

        self.assertEqual(12, tex.texture_info.size(False))
        self.assertEqual(12 + HEAD, tex.texture_info.size())

        self.assertEqual(30, tex.size(False))
        self.assertEqual(30 + HEAD, tex.size())

    def test_write_read_xml(self):
        self.write_read_xml_test(get_texture(), 'Texture', Texture.parse, compare_textures)
