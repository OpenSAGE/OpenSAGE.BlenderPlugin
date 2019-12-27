# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from io_mesh_w3d.structs.w3d_triangle import *


def get_triangle(vert_ids=(1, 2, 3),
                 surface_type=66,
                 normal=Vector((1.0, 22.0, -5.0)),
                 distance=103.0):
    return Triangle(
        vert_ids=vert_ids,
        surface_type=surface_type,
        normal=normal,
        distance=distance)


def compare_triangles(self, expected, actual, is_skin=False):
    self.assertEqual(expected.vert_ids, actual.vert_ids)
    self.assertEqual(expected.surface_type, actual.surface_type)

    if not is_skin:  # generated/changed by blender
        self.assertEqual(expected.normal, actual.normal)
        self.assertAlmostEqual(expected.distance, actual.distance, 1)
