# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_mesh_triangle import MeshTriangle

class TestMeshTriangle(unittest.TestCase):
    def test_write_read(self):
        expected = MeshTriangle(
            vert_ids=(1, 2, 3),
            surface_type=66,
            normal=Vector((1.0, 22.0, -5.0)),
            distance=103.0)

        self.assertEqual(32, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = MeshTriangle.read(io_stream)

        self.assertEqual(expected.vert_ids, actual.vert_ids)
        self.assertEqual(expected.surface_type, actual.surface_type)
        self.assertEqual(expected.normal, actual.normal)
        self.assertEqual(expected.distance, actual.distance)

