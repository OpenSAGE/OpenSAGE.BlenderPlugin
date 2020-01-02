# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector, Quaternion
from tests.mathutils import *
from io_mesh_w3d.w3x.structs.hierarchy import *
from tests.utils import almost_equal


def get_hierarchy_pivot(name="pivot", name_id=0, parent=1):
    return HierarchyPivot(
        name=name,
        name_id=name_id,
        parent_id=parent,
        translation=get_vector(22.0, 33.0, 1.0),
        rotation=get_quat(0.86, 0.25, -0.25, 0.36),
        fixup_matrix=get_mat([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]))


def compare_hierarchy_pivots(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.name_id, actual.name_id)
    self.assertEqual(expected.parent_id, actual.parent_id)

    self.assertAlmostEqual(expected.translation[0], actual.translation[0], 1)
    self.assertAlmostEqual(expected.translation[1], actual.translation[1], 1)
    self.assertAlmostEqual(expected.translation[2], actual.translation[2], 1)

    compare_quats(self, expected.rotation, actual.rotation)
    compare_mats(self, expected.fixup_matrix, actual.fixup_matrix)


def get_hierarchy(id="TestHierarchy"):
    hierarchy = Hierarchy(
        id=id,
        pivots=[])

    hierarchy.pivots = [get_hierarchy_pivot("ROOTTRANSFORM", parent=-1),
                        get_hierarchy_pivot("waist", parent=0),
                        get_hierarchy_pivot("hip", parent=1),
                        get_hierarchy_pivot("shoulderl", parent=2),
                        get_hierarchy_pivot("arml", parent=3),
                        get_hierarchy_pivot("shield", parent=4),
                        get_hierarchy_pivot("armr", parent=3),
                        get_hierarchy_pivot("sword", parent=0),
                        get_hierarchy_pivot(name_id=4, parent=0)]

    return hierarchy


def get_hierarchy_minimal():
    return Hierarchy(
        id="",
        pivots=[get_hierarchy_pivot()])


def compare_hierarchies(self, expected, actual):
    self.assertEqual(expected.id, actual.id)

    self.assertEqual(len(expected.pivots), len(actual.pivots))
    for i in range(len(expected.pivots)):
        compare_hierarchy_pivots(self, expected.pivots[i], actual.pivots[i])
