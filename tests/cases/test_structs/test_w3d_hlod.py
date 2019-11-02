# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from io_mesh_w3d.structs.w3d_hlod import HLod, HLodHeader, W3D_CHUNK_HLOD
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_hlod import *


class TestHLod(unittest.TestCase):
    def test_write_read(self):
        expected = get_hlod()

        self.assertEqual(48, expected.header.size())
        self.assertEqual(248, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HLOD, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = HLod.read(self, io_stream, chunkEnd)
        compare_hlods(self, expected, actual)

    def test_chunk_sizes(self):
        hlod = get_hlod_minimal()

        self.assertEqual(40, hlod.header.size(False))
        self.assertEqual(48, hlod.header.size())

        self.assertEqual(8, hlod.lod_array.header.size(False))
        self.assertEqual(16, hlod.lod_array.header.size())

        self.assertEqual(36, hlod.lod_array.sub_objects[0].size(False))
        self.assertEqual(44, hlod.lod_array.sub_objects[0].size())

        self.assertEqual(60, hlod.lod_array.size(False))
        self.assertEqual(68, hlod.lod_array.size())

        self.assertEqual(116, hlod.size())
