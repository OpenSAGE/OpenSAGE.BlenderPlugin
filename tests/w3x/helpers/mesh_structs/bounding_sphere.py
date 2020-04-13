# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3x.structs.mesh_structs.bounding_sphere import *


def get_sphere():
    return BoundingSphere(
        radius=9.314,
        center=Vector((2.0, 4.0, 3.33)))


def compare_spheres(self, expected, actual):
    self.assertEqual(expected.radius, actual.radius)
    self.assertEqual(expected.center, actual.center)