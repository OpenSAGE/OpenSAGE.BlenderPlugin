# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.w3d.helpers.mesh_structs.prelit import *


class TestPrelit(TestCase):
    def test_write_read(self):
        type = W3D_CHUNK_PRELIT_VERTEX
        expected = get_prelit(type=type)

        self.assertEqual(665, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, _) = read_chunk_head(io_stream)
        self.assertEqual(type, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = PrelitBase.read(self, io_stream, chunkSize, type)
        compare_prelits(self, expected, actual)

    def test_write_read_minimal(self):
        type = W3D_CHUNK_PRELIT_VERTEX
        expected = get_prelit_minimal(type=type)

        self.assertEqual(32, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, _) = read_chunk_head(io_stream)
        self.assertEqual(type, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = PrelitBase.read(self, io_stream, chunkSize, type)
        compare_prelits(self, expected, actual)

    def test_chunk_size(self):
        type = W3D_CHUNK_PRELIT_VERTEX
        expected = get_prelit(type=type)

        self.assertEqual(657, expected.size(False))
        self.assertEqual(665, expected.size())

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_PRELIT_VERTEX, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_PRELIT_VERTEX, chunk_type)

        self.warning = lambda text: self.assertEqual('unknown chunk_type in io_stream: 0x0', text)
        PrelitBase.read(self, io_stream, subchunk_end, W3D_CHUNK_PRELIT_VERTEX)
