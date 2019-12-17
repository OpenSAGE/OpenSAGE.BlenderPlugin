# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.helpers.w3d_vertex_influence import *


class TestVertexInfluence(TestCase):
    def test_write_read(self):
        expected = get_vertex_influence()

        self.assertEqual(8, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = VertexInfluence.read(io_stream)
        compare_vertex_influences(self, expected, actual)
