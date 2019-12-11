# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector, Quaternion

from io_mesh_w3d.structs_w3x.w3x_hierarchy import *
from tests.utils import almost_equal


def get_hierarchy_pivot(name="pivot", name_id=0, parent=1):
    return HierarchyPivot(
        name=name,
        name_id=name_id,
        parent_id=parent,
        translation=Vector((22.0, 33.0, 1.0)),
        rotation=Quaternion((0.86, 0.25, -0.25, 0.36)),
        fixup_matrix=Matrix(([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12])))


def compare_hierarchy_pivots(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.name_id, actual.name_id)
    self.assertEqual(expected.parent_id, actual.parent_id)

    self.assertAlmostEqual(expected.translation[0], actual.translation[0], 1)
    self.assertAlmostEqual(expected.translation[1], actual.translation[1], 1)
    self.assertAlmostEqual(expected.translation[2], actual.translation[2], 1)

    almost_equal(self, expected.rotation[0], actual.rotation[0], 0.2)
    almost_equal(self, expected.rotation[1], actual.rotation[1], 0.2)
    almost_equal(self, expected.rotation[2], actual.rotation[2], 0.2)
    almost_equal(self, expected.rotation[3], actual.rotation[3], 0.2)


    almost_equal(self, expected.fixup_matrix[0][0], actual.fixup_matrix[0][0], 0.2)
    almost_equal(self, expected.fixup_matrix[1][0], actual.fixup_matrix[1][0], 0.2)
    almost_equal(self, expected.fixup_matrix[2][0], actual.fixup_matrix[2][0], 0.2)
    almost_equal(self, expected.fixup_matrix[3][0], actual.fixup_matrix[3][0], 0.2)

    almost_equal(self, expected.fixup_matrix[0][1], actual.fixup_matrix[0][1], 0.2)
    almost_equal(self, expected.fixup_matrix[1][1], actual.fixup_matrix[1][1], 0.2)
    almost_equal(self, expected.fixup_matrix[2][1], actual.fixup_matrix[2][1], 0.2)
    almost_equal(self, expected.fixup_matrix[3][1], actual.fixup_matrix[3][1], 0.2)

    almost_equal(self, expected.fixup_matrix[0][2], actual.fixup_matrix[0][2], 0.2)
    almost_equal(self, expected.fixup_matrix[1][2], actual.fixup_matrix[1][2], 0.2)
    almost_equal(self, expected.fixup_matrix[2][2], actual.fixup_matrix[2][2], 0.2)
    almost_equal(self, expected.fixup_matrix[3][2], actual.fixup_matrix[3][2], 0.2)


def get_hierarchy(id="TestHierarchy"):
    hierarchy = Hierarchy(
        id=id,
        pivots=[])

    hierarchy.pivots.append(get_hierarchy_pivot("ROOTTRANSFORM", parent=-1))
    hierarchy.pivots.append(get_hierarchy_pivot("waist", parent=0))
    hierarchy.pivots.append(get_hierarchy_pivot("hip", parent=1))
    hierarchy.pivots.append(get_hierarchy_pivot("shoulderl", parent=2))
    hierarchy.pivots.append(get_hierarchy_pivot("arml", parent=3))
    hierarchy.pivots.append(get_hierarchy_pivot("shield", parent=4))
    hierarchy.pivots.append(get_hierarchy_pivot("armr", parent=3))
    hierarchy.pivots.append(get_hierarchy_pivot("sword", parent=0))
    hierarchy.pivots.append(get_hierarchy_pivot(name_id=4, parent=0))

    return hierarchy


def get_hierarchy_minimal():
    return Hierarchy(
        id="",
        pivots=[get_hierarchy_pivot()])


def get_hierarchy_empty():
    return Hierarchy(
        id="",
        pivots=[])


def compare_hierarchies(self, expected, actual):
    self.assertEqual(expected.id, actual.id)

    self.assertEqual(len(expected.pivots), len(actual.pivots))
    for i in range(len(expected.pivots)):
        compare_hierarchy_pivots(self, expected.pivots[i], actual.pivots[i])
