# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.w3x.helpers.mesh_structs.bounding_box import *
from tests.utils import TestCase


class TestBoundingBox(TestCase):
    def test_write_read_xml(self):
        expected = get_box()

        root = create_root()
        expected.create(root)

        io_stream = io.BytesIO()
        write(root, io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        root = find_root(self, io_stream)
        xml_boxes = root.findall('BoundingBox')
        self.assertEqual(1, len(xml_boxes))

        actual = BoundingBox.parse(self, xml_boxes[0])
        compare_boxes(self, expected, actual)
