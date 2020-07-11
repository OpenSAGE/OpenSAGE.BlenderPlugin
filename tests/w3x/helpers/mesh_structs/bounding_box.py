# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3x.structs.mesh_structs.bounding_box import *


def get_box():
    return BoundingBox(
        min=Vector((1.0, -2.0, 3.0)),
        max=Vector((2.0, 4.0, 3.33)))


def compare_boxes(self, expected, actual):
    self.assertEqual(expected.min, actual.min)
    self.assertEqual(expected.max, actual.max)
