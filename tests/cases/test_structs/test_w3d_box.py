# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_box import Box, W3D_CHUNK_BOX
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import read_chunk_head


class TestBox(unittest.TestCase):
    def test_write_read(self):
        expected = Box()
        expected.version = Version(major=5, minor=22)
        expected.box_type = 3
        expected.collision_types = 64
        expected.name = "TestBoxxx"
        expected.color = RGBA(r=125, g=110, b=55, a=244)
        expected.center = Vector((1.0, 2.0, 3.0))
        expected.extend = Vector((4.0, 5.0, 6.0))

        self.assertEqual(68, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, _) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_BOX, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = Box.read(io_stream)
        self.assertEqual(expected.version.major, actual.version.major)
        self.assertEqual(expected.version.minor, actual.version.minor)
        self.assertEqual(expected.box_type, actual.box_type)
        self.assertEqual(expected.collision_types, actual.collision_types)
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.color, actual.color)

        self.assertEqual(expected.center.x, actual.center.x)
        self.assertEqual(expected.center.y, actual.center.y)
        self.assertEqual(expected.center.z, actual.center.z)

        self.assertEqual(expected.extend.x, actual.extend.x)
        self.assertEqual(expected.extend.y, actual.extend.y)
        self.assertEqual(expected.extend.z, actual.extend.z)
