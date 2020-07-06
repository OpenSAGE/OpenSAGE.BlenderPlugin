# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from tests.w3x.helpers.mesh_structs.bounding_sphere import *
from tests.utils import TestCase


class TestBoundingSphere(TestCase):
    def test_write_read_xml(self):
        self.write_read_xml_test(get_sphere(), 'BoundingSphere', BoundingSphere.parse, compare_spheres)