# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.helpers.w3d_triangle import *


class TestTriangle(TestCase):
    def test_write_read(self):
        expected = get_triangle()

        self.assertEqual(32, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = Triangle.read(io_stream)
        compare_triangles(self, expected, actual)
