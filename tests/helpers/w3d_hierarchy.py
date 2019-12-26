# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector, Quaternion

from io_mesh_w3d.structs.w3d_hierarchy import Hierarchy, HierarchyHeader, HierarchyPivot

from tests.helpers.w3d_version import get_version, compare_versions
from tests.utils import almost_equal


def get_hierarchy_header(name="TestHierarchy"):
    return HierarchyHeader(
        version=get_version(),
        name=name,
        num_pivots=0,
        center_pos=Vector((0.0, 0.0, 0.0)))


def compare_hierarchy_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.num_pivots, actual.num_pivots)
    self.assertEqual(expected.center_pos, actual.center_pos)


def get_hierarchy_pivot(name="pivot", parent=1):
    return HierarchyPivot(
        name=name,
        parent_id=parent,
        translation=Vector((22.0, 33.0, 1.0)),
        euler_angles=Vector((0.32, -0.65, 0.67)),
        rotation=Quaternion((0.86, 0.25, -0.25, 0.36)))


def get_roottransform():
    return HierarchyPivot(
        name="ROOTTRANSFORM",
        parent_id=-1,
        translation=Vector(),
        euler_angles=Vector(),
        rotation=Quaternion())


def compare_hierarchy_pivots(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.parent_id, actual.parent_id)

    self.assertAlmostEqual(expected.translation[0], actual.translation[0], 1)
    self.assertAlmostEqual(expected.translation[1], actual.translation[1], 1)
    self.assertAlmostEqual(expected.translation[2], actual.translation[2], 1)

    #almost_equal(self, expected.euler_angles.x, actual.euler_angles.x, 0.2)
    #almost_equal(self, expected.euler_angles.y, actual.euler_angles.y, 0.2)
    #almost_equal(self, expected.euler_angles.z, actual.euler_angles.z, 0.2)

    almost_equal(self, expected.rotation[0], actual.rotation[0], 0.2)
    almost_equal(self, expected.rotation[1], actual.rotation[1], 0.2)
    almost_equal(self, expected.rotation[2], actual.rotation[2], 0.2)
    almost_equal(self, expected.rotation[3], actual.rotation[3], 0.2)


def get_hierarchy(name="TestHierarchy"):
    hierarchy = Hierarchy(
        header=get_hierarchy_header(name),
        pivots=[],
        pivot_fixups=[])

    hierarchy.pivots.append(get_roottransform())
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.pivots.append(get_hierarchy_pivot("waist", 0))
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.pivots.append(get_hierarchy_pivot("hip", 1))
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.pivots.append(get_hierarchy_pivot("shoulderl", 2))
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.pivots.append(get_hierarchy_pivot("arml", 3))
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.pivots.append(get_hierarchy_pivot("shield", 4))
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.pivots.append(get_hierarchy_pivot("armr", 3))
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.pivots.append(get_hierarchy_pivot("sword", 0))
    hierarchy.pivot_fixups.append(Vector())

    hierarchy.header.num_pivots = len(hierarchy.pivots)

    return hierarchy


def get_hierarchy_minimal():
    return Hierarchy(
        header=get_hierarchy_header(),
        pivots=[get_hierarchy_pivot()],
        pivot_fixups=[Vector()])


def get_hierarchy_empty():
    return Hierarchy(
        header=get_hierarchy_header(),
        pivots=[],
        pivot_fixups=[])


def compare_hierarchies(self, expected, actual):
    compare_hierarchy_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.pivots), len(actual.pivots))
    for i in range(len(expected.pivots)):
        compare_hierarchy_pivots(self, expected.pivots[i], actual.pivots[i])

    self.assertEqual(len(expected.pivot_fixups), len(actual.pivot_fixups))
    for i in range(len(expected.pivot_fixups)):
        self.assertEqual(expected.pivot_fixups[i], actual.pivot_fixups[i])
