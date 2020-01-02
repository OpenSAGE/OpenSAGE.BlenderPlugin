# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from tests.mathutils import *
from io_mesh_w3d.w3d.structs.hierarchy import *
from tests.w3d.helpers.version import get_version, compare_versions
from tests.utils import almost_equal


def get_hierarchy_header(name="TestHierarchy"):
    return HierarchyHeader(
        version=get_version(),
        name=name,
        num_pivots=0,
        center_pos=get_vector(0.0, 0.0, 0.0))


def compare_hierarchy_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.num_pivots, actual.num_pivots)
    compare_vectors(self, expected.center_pos, actual.center_pos)


def get_hierarchy_pivot(name="pivot", parent=1):
    return HierarchyPivot(
        name=name,
        parent_id=parent,
        translation=get_vector(22.0, 33.0, 1.0),
        euler_angles=get_vector(0.32, -0.65, 0.67),
        rotation=get_quat(0.86, 0.25, -0.25, 0.36))


def get_roottransform():
    return HierarchyPivot(
        name="ROOTTRANSFORM",
        parent_id=-1,
        translation=get_vector(),
        euler_angles=get_vector(),
        rotation=get_quat())


def compare_hierarchy_pivots(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.parent_id, actual.parent_id)

    compare_vectors(self, expected.translation, actual.translation)

    # dont care for those
    #compare_vectors(self, expected.euler_angles, actual.euler_angles)

    compare_quats(self, expected.rotation, actual.rotation)


def get_hierarchy(name="TestHierarchy"):
    hierarchy = Hierarchy(
        header=get_hierarchy_header(name),
        pivots=[],
        pivot_fixups=[])

    hierarchy.pivots.append(get_roottransform())
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.pivots.append(get_hierarchy_pivot("b_waist", 0))
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.pivots.append(get_hierarchy_pivot("b_hip", 1))
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.pivots.append(get_hierarchy_pivot("shoulderl", 2))
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.pivots.append(get_hierarchy_pivot("arml", 3))
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.pivots.append(get_hierarchy_pivot("armr", 3))
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.pivots.append(get_hierarchy_pivot("TRUNK", 5))
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.pivots.append(get_hierarchy_pivot("B_SWORD", 0))
    hierarchy.pivot_fixups.append(get_vector())

    hierarchy.header.num_pivots = len(hierarchy.pivots)

    return hierarchy


def get_hierarchy_minimal():
    return Hierarchy(
        header=get_hierarchy_header(),
        pivots=[get_hierarchy_pivot()],
        pivot_fixups=[get_vector()])


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
        compare_vectors(self, expected.pivot_fixups[i], actual.pivot_fixups[i])
