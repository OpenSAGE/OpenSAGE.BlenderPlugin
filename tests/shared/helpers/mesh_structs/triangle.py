# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.shared.structs.mesh_structs.triangle import *
from tests.mathutils import *


def get_triangle(vert_ids=[1, 2, 3],
                 surface_type=13,
                 normal=get_vec(x=1.0, y=22.0, z=-5.0),
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
