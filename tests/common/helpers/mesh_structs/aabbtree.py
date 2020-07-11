# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.mesh_structs.aabbtree import *
from tests.mathutils import *


def get_aabbtree_header(num_nodes=33, num_polys=41):
    return AABBTreeHeader(
        node_count=num_nodes,
        poly_count=num_polys)


def compare_aabbtree_headers(self, expected, actual):
    self.assertEqual(expected.node_count, actual.node_count)
    self.assertEqual(expected.poly_count, actual.poly_count)


def get_aabbtree_poly_indices(num_polys=41):
    result = []
    for i in range(num_polys):
        result.append(i)
    return result


def get_aabbtree_node(xml=False, i=0):
    node = AABBTreeNode(
        min=get_vec(1.0, 2.0, 3.0),
        max=get_vec(4.0, 5.0, 6.0))

    if xml and i % 2 == 0:
        node.polys = Polys(begin=3, count=44)
    else:
        node.children = Children(front=5, back=9)
    return node


def compare_aabbtree_nodes(self, expected, actual):
    compare_vectors(self, expected.min, actual.min)
    compare_vectors(self, expected.max, actual.max)
    if expected.children is not None:
        self.assertEqual(expected.children.front, actual.children.front)
        self.assertEqual(expected.children.front, actual.children.front)
    if expected.polys is not None:
        self.assertEqual(expected.polys.begin, actual.polys.begin)
        self.assertEqual(expected.polys.count, actual.polys.count)


def get_aabbtree_nodes(num_nodes=33, xml=False):
    nodes = []
    for i in range(num_nodes):
        nodes.append(get_aabbtree_node(xml, i))
    return nodes


def get_aabbtree(num_nodes=33, num_polys=41, xml=False):
    return AABBTree(
        header=get_aabbtree_header(num_nodes, num_polys),
        poly_indices=get_aabbtree_poly_indices(num_polys),
        nodes=get_aabbtree_nodes(num_nodes, xml))


def get_aabbtree_minimal():
    return AABBTree(
        header=get_aabbtree_header(num_nodes=1, num_polys=1),
        poly_indices=[1],
        nodes=[get_aabbtree_node()])


def get_aabbtree_empty():
    return AABBTree(header=get_aabbtree_header(num_nodes=0, num_polys=0))


def compare_aabbtrees(self, expected, actual):
    compare_aabbtree_headers(self, expected.header, actual.header)
    self.assertEqual(len(expected.poly_indices), len(actual.poly_indices))
    self.assertEqual(expected.poly_indices, actual.poly_indices)

    self.assertEqual(len(expected.nodes), len(actual.nodes))
    for i in range(len(expected.nodes)):
        compare_aabbtree_nodes(self, expected.nodes[i], actual.nodes[i])
