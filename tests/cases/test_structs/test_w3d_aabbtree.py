# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_aabbtree import MeshAABBTree, AABBTreeHeader, AABBTreeNode, W3D_CHUNK_AABBTREE
from io_mesh_w3d.io_binary import read_chunk_head


class TestAABBTree(unittest.TestCase):
    def test_write_read(self):
        expected = MeshAABBTree()
        expected.header = AABBTreeHeader(
            node_count=55,
            poly_count=22)

        self.assertEqual(8, expected.header.size_in_bytes())

        expected.poly_indices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        node1 = AABBTreeNode(
            min=Vector((1.0, 2.0, 3.0)),
            max=Vector((4.0, 5.0, 6.0)),
            front_or_poly_0=34,
            back_or_poly_count=123)

        self.assertEqual(32, node1.size_in_bytes())

        node2 = AABBTreeNode(
            min=Vector((1.0, 2.0, 3.0)),
            max=Vector((4.0, 5.0, 6.0)),
            front_or_poly_0=21,
            back_or_poly_count=665)

        self.assertEqual(32, node2.size_in_bytes())

        expected.nodes.append(node1)
        expected.nodes.append(node2)

        self.assertEqual(136, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_AABBTREE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = MeshAABBTree.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.header.node_count, actual.header.node_count)
        self.assertEqual(expected.header.poly_count, actual.header.poly_count)

        self.assertEqual(expected.poly_indices, actual.poly_indices)

        self.assertEqual(len(expected.nodes), len(actual.nodes))

        for i, node in enumerate(expected.nodes):
            self.assertEqual(node.min, actual.nodes[i].min)
            self.assertEqual(node.max, actual.nodes[i].max)
            self.assertEqual(node.front_or_poly_0, actual.nodes[i].front_or_poly_0)
            self.assertEqual(node.back_or_poly_count, actual.nodes[i].back_or_poly_count)
