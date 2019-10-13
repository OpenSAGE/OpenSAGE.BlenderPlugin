# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from mathutils import Vector
from io_mesh_w3d.structs.w3d_aabbtree import AABBTree, AABBTreeHeader, AABBTreeNode, W3D_CHUNK_AABBTREE

def get_aabbtree_header(num_nodes=33, num_polys=41):
    return AABBTreeHeader(
        node_count=num_nodes,
        poly_count=num_polys)

def get_aabbtree_poly_indices(num_polys=41):
    result = []
    for i in range(num_polys):
        result.append(i)
    return result

def get_aabbtree_node():
    return AABBTreeNode(
        min=Vector((1.0, 2.0, 3.0)),
        max=Vector((4.0, 5.0, 6.0)),
        front_or_poly_0=34,
        back_or_poly_count=123)

def get_aabbtree_nodes(num_nodes=33):
    nodes = []
    for _ in range(num_nodes):
        nodes.append(get_aabbtree_node())
    return nodes

def get_aabbtree(num_nodes=33, num_polys=41):
    return AABBTree(
        header=get_aabbtree_header(num_nodes, num_polys),
        poly_indices=get_aabbtree_poly_indices(num_polys),
        nodes=get_aabbtree_nodes(num_nodes))

def compare_aabbtree_headers(self, expected, actual):
    self.assertEqual(expected.node_count, actual.node_count)
    self.assertEqual(expected.poly_count, actual.poly_count)

def compare_aabbtree_nodes(self, expected, actual):
    self.assertEqual(expected.min, actual.min)
    self.assertEqual(expected.max, actual.max)
    self.assertEqual(expected.front_or_poly_0, actual.front_or_poly_0)
    self.assertEqual(expected.back_or_poly_count, actual.back_or_poly_count)

def compare_aabbtrees(self, expected, actual):
    compare_aabbtree_headers(self, expected.header, actual.header)
    self.assertEqual(len(expected.poly_indices), len(actual.poly_indices))
    for i in range(len(expected.poly_indices)):
        self.assertEqual(expected.poly_indices[i], actual.poly_indices[i])

    self.assertEqual(len(expected.nodes), len(actual.nodes))
    for i in range(len(expected.nodes)):
        compare_aabbtree_nodes(self, expected.nodes[i], actual.nodes[i])



