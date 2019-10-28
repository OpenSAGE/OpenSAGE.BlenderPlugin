# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from mathutils import Vector
from io_mesh_w3d.structs.w3d_triangle import Triangle

def get_triangle():
    return Triangle(
        vert_ids=(1, 2, 3),
        surface_type=66,
        normal=Vector((1.0, 22.0, -5.0)),
        distance=103.0)

def compare_triangles(self, expected, actual):
    self.assertEqual(expected.vert_ids, actual.vert_ids)
    self.assertEqual(expected.surface_type, actual.surface_type)
    print("#")
    print(str(expected.normal) + " -> " + str(actual.normal))
    print(str(expected.distance) + " -> " + str(actual.distance))
    #self.assertEqual(expected.normal, actual.normal)
    #self.assertAlmostEqual(expected.distance, actual.distance, 1)
