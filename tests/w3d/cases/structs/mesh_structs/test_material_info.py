# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.utils import TestCase
from tests.w3d.helpers.mesh_structs.material_info import *


class TestMaterialInfo(TestCase):
    def test_write_read(self):
        expected = get_material_info()

        self.assertEqual(24, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_INFO, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = MaterialInfo.read(io_stream)

        compare_material_infos(self, expected, actual)

    def test_chunk_size(self):
        expected = get_material_info()

        self.assertEqual(16, expected.size(False))
        self.assertEqual(24, expected.size())
