# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from mathutils import Vector, Quaternion

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_hierarchy import Hierarchy, HierarchyHeader, \
    HierarchyPivot

def get_hierarchy_header(name):
    return HierarchyHeader(
        version=Version(major=4, minor=1),
        name=name,
        num_pivots=0,
        center_pos=Vector((2.0, 3.0, 1.0)))

def compare_hierarchy_headers(self, expected, actual):
    self.assertEqual(expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.num_pivots, actual.num_pivots)
    self.assertEqual(expected.center_pos, actual.center_pos)

def get_hierarchy_pivot(name, parent):
    return HierarchyPivot(
        name=name,
        parent_id=parent,
        translation=Vector((22.0, 33.0, 1.0)),
        euler_angles=Vector((1.0, 12.0, -2.0)),
        rotation=Quaternion((1.0, -0.1, -0.2, -0.3)))

def compare_hierarchy_pivots(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.parent_id, actual.parent_id)
    self.assertEqual(expected.translation, actual.translation)
    self.assertEqual(expected.euler_angles, actual.euler_angles)
    self.assertEqual(expected.rotation, actual.rotation)

def get_hierarchy(name="TestHierarchy", minimal=False):
    hierarchy = Hierarchy(
        header=get_hierarchy_header(name),
        pivots=[],
        pivot_fixups=[])

    if minimal:
        return hierarchy

    hierarchy.pivots.append(get_hierarchy_pivot("Roottransform", -1))
    hierarchy.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))

    hierarchy.pivots.append(get_hierarchy_pivot("waist", 0))
    hierarchy.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))

    hierarchy.pivots.append(get_hierarchy_pivot("hip", 1))
    hierarchy.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))

    hierarchy.pivots.append(get_hierarchy_pivot("shoulderl", 2))
    hierarchy.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))

    hierarchy.pivots.append(get_hierarchy_pivot("arml", 3))
    hierarchy.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))


    hierarchy.pivots.append(get_hierarchy_pivot("shield", 4))
    hierarchy.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))

    hierarchy.pivots.append(get_hierarchy_pivot("sword", 0))
    hierarchy.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))

    hierarchy.header.pivot_count = len(hierarchy.pivots)

    return hierarchy

def compare_hierarchies(self, expected, actual):
    compare_hierarchy_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.pivots), len(actual.pivots))
    for i in range(len(expected.pivots)):
        compare_hierarchy_pivots(self, expected.pivots[i], actual.pivots[i])

    self.assertEqual(len(expected.pivot_fixups), len(actual.pivot_fixups))
    for i  in range(len(expected.pivot_fixups)):
        self.assertEqual(expected.pivot_fixups[i], actual.pivot_fixups[i])

