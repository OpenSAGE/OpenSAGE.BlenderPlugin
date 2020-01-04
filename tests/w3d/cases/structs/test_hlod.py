# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.w3d.helpers.hlod import *


class TestHLod(TestCase):
    def test_write_read(self):
        expected = get_hlod()

        self.assertEqual(48, expected.header.size())
        self.assertEqual(292, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HLOD, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = HLod.read(self, io_stream, chunkEnd)
        compare_hlods(self, expected, actual)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_HLOD, output, 26, has_sub_chunks=True)

        write_chunk_head(W3D_CHUNK_HLOD_LOD_ARRAY,
                         output, 9, has_sub_chunks=True)
        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_HLOD, chunk_type)

        HLod.read(self, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        hlod = get_hlod_minimal()

        self.assertEqual(40, hlod.header.size(False))
        self.assertEqual(48, hlod.header.size())

        self.assertEqual(8, hlod.lod_arrays[0].header.size(False))
        self.assertEqual(16, hlod.lod_arrays[0].header.size())

        self.assertEqual(36, hlod.lod_arrays[0].sub_objects[0].size(False))
        self.assertEqual(44, hlod.lod_arrays[0].sub_objects[0].size())

        self.assertEqual(60, hlod.lod_arrays[0].size(False))
        self.assertEqual(68, hlod.lod_arrays[0].size())

        self.assertEqual(116, hlod.size())
