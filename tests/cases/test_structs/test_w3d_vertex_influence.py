# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_vertex_influence import VertexInfluence
from tests.helpers.w3d_vertex_influence import get_vertex_influence, compare_vertex_influences


class TestVertexInfluence(unittest.TestCase):
    def test_write_read(self):
        expected = get_vertex_influence()

        self.assertEqual(8, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = VertexInfluence.read(io_stream)
        compare_vertex_influences(self, expected, actual)
