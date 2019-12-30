# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.helpers.w3d_dazzle import *


class TestDazzle(TestCase):
    def test_write_read(self):
        expected = get_dazzle()

        self.assertEqual(38, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_DAZZLE, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = Dazzle.read(self, io_stream, chunkEnd)

        compare_dazzles(self, expected, actual)


    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_DAZZLE, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_DAZZLE, chunk_type)

        Dazzle.read(self, io_stream, subchunk_end)


    def test_chunk_sizes(self):
        dazzle = get_dazzle()

        self.assertEqual(38, dazzle.size())
        self.assertEqual(30, dazzle.size(False))
