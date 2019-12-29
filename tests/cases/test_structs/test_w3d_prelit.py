# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io
from tests.utils import TestCase
from io_mesh_w3d.io_binary import read_chunk_head
from tests.helpers.w3d_prelit import *


class TestPrelit(TestCase):
    def test_write_read(self):
        type = W3D_CHUNK_PRELIT_VERTEX
        expected = get_prelit(type=type)

        self.assertEqual(566, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, _) = read_chunk_head(io_stream)
        self.assertEqual(type, chunkType)
        self.assertEqual(expected.size(), chunkSize)

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
        self.assertEqual(expected.size(), chunkSize)

        actual = PrelitBase.read(self, io_stream, chunkSize, type)
        compare_prelits(self, expected, actual)
