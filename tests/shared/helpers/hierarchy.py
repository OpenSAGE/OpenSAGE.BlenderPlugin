# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from tests.mathutils import *
from io_mesh_w3d.shared.structs.hierarchy import *
from tests.w3d.helpers.version import get_version, compare_versions
from tests.utils import almost_equal


def get_hierarchy_header(name="TestHierarchy", xml=False):
    if xml:
        return None
    return HierarchyHeader(
        version=get_version(),
        name=name,
        num_pivots=0,
        center_pos=get_vec(0.0, 0.0, 0.0))


def compare_hierarchy_headers(self, expected, actual):
    if expected is None:
        self.assertIsNone(actual)
        return

    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.num_pivots, actual.num_pivots)
    compare_vectors(self, expected.center_pos, actual.center_pos)


def get_hierarchy_pivot(name="pivot", name_id=0, parent=1):
    return HierarchyPivot(
        name=name,
        name_id=name_id,
        parent_id=parent,
        translation=get_vec(22.0, 33.0, 1.0),
        euler_angles=get_vec(0.32, -0.65, 0.67),
        rotation=get_quat(0.86, 0.25, -0.25, 0.36),
        fixup_matrix=get_mat([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]))


def get_roottransform():
    return HierarchyPivot(
        name="ROOTTRANSFORM",
        name_id=0,
        parent_id=-1,
        translation=get_vec(),
        euler_angles=get_vec(),
        rotation=get_quat(),
        fixup_matrix=get_mat())


def compare_hierarchy_pivots(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.name_id, actual.name_id)
    self.assertEqual(expected.parent_id, actual.parent_id)

    compare_vectors(self, expected.translation, actual.translation)
    # dont care for those
    #compare_vectors(self, expected.euler_angles, actual.euler_angles)
    compare_quats(self, expected.rotation, actual.rotation)
    compare_mats(self, expected.fixup_matrix, actual.fixup_matrix)


def get_hierarchy(name="TestHierarchy", xml=False):
    hierarchy = Hierarchy(
        header=None,
        id=name,
        pivots=[],
        pivot_fixups=[])

    if xml:
        hierarchy.id = name
    else:
        hierarchy.header = get_hierarchy_header(name)
        hierarchy.pivot_fixups = [
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec()]

    hierarchy.pivots = [
        get_roottransform(),
        get_hierarchy_pivot(name="b_waist", parent=0),
        get_hierarchy_pivot(name="b_hip", parent=1),
        get_hierarchy_pivot(name="shoulderl", parent=2),
        get_hierarchy_pivot(name="arml", parent=3),
        get_hierarchy_pivot(name="armr", parent=3),
        get_hierarchy_pivot(name="TRUNK", parent=5),
        get_hierarchy_pivot(name="sword", parent=0)]

    if xml:
        hierarchy.pivots.append(
            get_hierarchy_pivot(name_id=4, parent=0))
    else:
        hierarchy.header.num_pivots = len(hierarchy.pivots)

    return hierarchy


def get_hierarchy_minimal(xml=False):
    return Hierarchy(
        header=get_hierarchy_header(xml=xml),
        id="",
        pivots=[get_hierarchy_pivot()],
        pivot_fixups=[get_vec()])


def get_hierarchy_empty(xml=False):
    return Hierarchy(
        header=get_hierarchy_header(xml=xml),
        pivots=[],
        pivot_fixups=[])


def compare_hierarchies(self, expected, actual):
    compare_hierarchy_headers(self, expected.header, actual.header)

    self.assertEqual(expected.id, actual.id)

    self.assertEqual(len(expected.pivots), len(actual.pivots))
    for i in range(len(expected.pivots)):
        compare_hierarchy_pivots(self, expected.pivots[i], actual.pivots[i])

    self.assertEqual(len(expected.pivot_fixups), len(actual.pivot_fixups))
    for i in range(len(expected.pivot_fixups)):
        compare_vectors(self, expected.pivot_fixups[i], actual.pivot_fixups[i])
