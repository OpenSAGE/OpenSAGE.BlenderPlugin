# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector

from io_mesh_w3d.w3x.structs.mesh_structs.aabbtree import *
from tests.utils import almost_equal
from tests.mathutils import *


def get_children():
    return Children(
        front=3,
        back=44)


def compare_childrens(self, expected, actual):
    if expected is None and actual is None:
        return
    self.assertEqual(expected.front, actual.front)
    self.assertEqual(expected.back, actual.back)


def get_polys():
    return Polys(
        begin=5,
        count=54)


def compare_polys(self, expected, actual):
    if expected is None and actual is None:
        return
    self.assertEqual(expected.begin, actual.begin)
    self.assertEqual(expected.count, actual.count)


def get_node(polys=None, children=None):
    return Node(
        min=get_vec(3.1, 3.2, 0.2),
        max=get_vec(2.0, -1.0, 22.0),
        polys=polys,
        children=children)


def compare_nodes(self, expected, actual):
    almost_equal(self, expected.min[0], actual.min[0], 0.2)
    almost_equal(self, expected.min[1], actual.min[1], 0.2)
    almost_equal(self, expected.min[2], actual.min[2], 0.2)

    almost_equal(self, expected.max[0], actual.max[0], 0.2)
    almost_equal(self, expected.max[1], actual.max[1], 0.2)
    almost_equal(self, expected.max[2], actual.max[2], 0.2)

    compare_polys(self, expected.polys, actual.polys)
    compare_childrens(self, expected.children, actual.children)


def get_aabbtree():
    return AABBTree(
        poly_indices=[1, 2, 33, 2, 3, 4, 5],
        nodes=[
            get_node(polys=get_polys()),
            get_node(polys=get_polys()),
            get_node(children=get_children()),
            get_node(children=get_children())])


def get_aabbtree_minimal():
    return AABBTree(
        poly_indices=[1],
        nodes=[get_node(polys=get_polys())])


def compare_aabbtrees(self, expected, actual):
    self.assertEqual(len(expected.poly_indices), len(actual.poly_indices))
    self.assertEqual(expected.poly_indices, actual.poly_indices)

    self.assertEqual(len(expected.nodes), len(actual.nodes))
    for i, node in enumerate(expected.nodes):
        compare_nodes(self, node, actual.nodes[i])
