# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector
from io_mesh_w3d.structs_w3d.w3d_triangle import Triangle


def get_triangle(vert_ids=[1, 2, 3],
                 surface_type=66,
                 normal=get_vector(x=1.0, y=22.0, z=-5.0),
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
        compare_vectors(self, expected.normal, actual.normal)
        self.assertAlmostEqual(expected.distance, actual.distance, 1)
