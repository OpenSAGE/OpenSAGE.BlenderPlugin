# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_mesh_vertex_influence import MeshVertexInfluence

class TestMeshVertexInfluence(unittest.TestCase):
    def test_write_read(self):
        expected = MeshVertexInfluence(
            bone_idx=33,
            xtra_idx=66,
            bone_inf=25.0,
            xtra_inf=75.0)

        self.assertEqual(8, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = MeshVertexInfluence.read(io_stream)

        self.assertEqual(33, actual.bone_idx)
        self.assertEqual(66, actual.xtra_idx)
        self.assertEqual(25.0, actual.bone_inf)
        self.assertEqual(75.0, actual.xtra_inf)

