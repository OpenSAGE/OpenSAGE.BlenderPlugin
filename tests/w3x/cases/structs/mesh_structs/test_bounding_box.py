# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.w3x.helpers.mesh_structs.bounding_box import *
from tests.utils import TestCase


class TestBoundingBox(TestCase):
    def test_write_read_xml(self):
        self.write_read_xml_test(get_box(), 'BoundingBox', BoundingBox.parse, compare_boxes)
