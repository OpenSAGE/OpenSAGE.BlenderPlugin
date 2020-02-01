# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.shared.helpers.mesh_structs.triangle import *
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
        expected = get_triangle()

        root = create_root()
        expected.create(root)

        io_stream = io.BytesIO()
        write(root, io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        root = find_root(self, io_stream)
        xml_triangles = root.findAll('T')
        self.assertEqual(1, len(xml_triangles))

        actual = Triangle.parse(self, xml_triangles[0])
        compare_triangles(self, expected, actual)
