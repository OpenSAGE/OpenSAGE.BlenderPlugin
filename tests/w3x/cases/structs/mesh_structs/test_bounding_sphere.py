# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.w3x.helpers.mesh_structs.bounding_sphere import *
from tests.utils import TestCase


class TestBoundingSphere(TestCase):
    def test_write_read_xml(self):
        expected = get_sphere()

        root = create_root()
        expected.create(root)

        io_stream = io.BytesIO()
        write(root, io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        root = find_root(self, io_stream)
        xml_spheres = root.findall('BoundingSphere')
        self.assertEqual(1, len(xml_spheres))

        actual = BoundingSphere.parse(self, xml_spheres[0])
        compare_spheres(self, expected, actual)