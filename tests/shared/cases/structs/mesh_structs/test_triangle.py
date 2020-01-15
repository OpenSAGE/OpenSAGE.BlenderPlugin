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

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_triangles = dom.getElementsByTagName('T')
        self.assertEqual(1, len(xml_triangles))

        actual = Triangle.parse(xml_triangles[0])
        compare_triangles(self, expected, actual)
