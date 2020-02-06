# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from shutil import copyfile

from io_mesh_w3d.common.utils.mesh_export import *
from tests.common.helpers.mesh import *
from tests.utils import *


class TestExportUtils(TestCase):
    def test_aabbtree_creation(self):
        expected = AABBTree(
            header=get_aabbtree_header(num_nodes=5, num_polys=10),
            poly_indices=[3, 6, 7, 8, 9, 1, 2, 5, 0, 4],
            nodes=[])

        expected.nodes = [
            AABBTreeNode(
                min=get_vec(-0.699, -0.743, -0.296),
                max=get_vec(0.684, 0.571, 0.203),
                polys=None,
                children=Children(front=1, back=2)),
            AABBTreeNode(
                min=get_vec(-0.699, -0.241, -0.296),
                max=get_vec(0.684, 0.571, 0.203),
                polys=Polys(begin=0, count=5),
                children=None),
            AABBTreeNode(
                min=get_vec(-0.699, -0.743, -0.296),
                max=get_vec(0.684, 0.165, 0.203),
                polys=None,
                children=Children(front=3, back=4)),
            AABBTreeNode(
                min=get_vec(-0.699, -0.743, -0.296),
                max=get_vec(0.684, -0.086, 0.203),
                polys=Polys(begin=5, count=4),
                children=None),
            AABBTreeNode(
                min=get_vec(-0.699, -0.241, -0.296),
                max=get_vec(-0.139, 0.165, 0.203),
                polys=Polys(begin=9, count=1),
                children=None)]

        verts = [get_vec(0.124, 0.165, -0.296),
                 get_vec(0.684, -0.241, 0.203),
                 get_vec(-0.007, -0.743, 0.203),
                 get_vec(-0.008, -0.241, -0.296),

                 get_vec(0.420, 0.571, 0.203),
                 get_vec(0.206, -0.084, -0.296),
                 get_vec(-0.434, 0.571, 0.203),
                 get_vec(-0.139, 0.165, -0.296),

                 get_vec(-0.699, -0.241, 0.203),

                 get_vec(-0.221, -0.086, -0.296)]

        actual = retrieve_aabbtree(verts)

        # compare_aabbtrees(self, expected, actual)
