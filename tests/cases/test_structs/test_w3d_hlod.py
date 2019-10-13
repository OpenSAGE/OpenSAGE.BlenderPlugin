# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_hlod import HLod, HLodHeader, W3D_CHUNK_HLOD
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_hlod import get_hlod, compare_hlods

class TestHLod(unittest.TestCase):
    def test_write_read(self):
        expected = get_hlod()

        self.assertEqual(40, expected.header.size_in_bytes())
        self.assertEqual(160, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HLOD, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = HLod.read(self, io_stream, chunkEnd)
        compare_hlods(self, expected, actual)