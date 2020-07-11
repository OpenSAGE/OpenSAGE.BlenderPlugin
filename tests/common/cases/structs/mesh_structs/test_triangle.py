# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.mesh_structs.triangle import *
from tests.utils import *


class TestTriangle(TestCase):
    def test_write_read_bin(self):
        expected = get_triangle()

        self.assertEqual(32, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = Triangle.read(io_stream)
        compare_triangles(self, expected, actual)

    def test_write_read_xml(self):
        self.write_read_xml_test(get_triangle(), 'T', Triangle.parse, compare_triangles)
