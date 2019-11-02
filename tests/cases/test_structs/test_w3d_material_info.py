# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import read_chunk_head
from tests.helpers.w3d_material_info import *


class TestMaterialInfo(unittest.TestCase):
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