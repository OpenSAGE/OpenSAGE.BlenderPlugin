# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import io
from shutil import copyfile
from os.path import dirname as up

from io_mesh_w3d.common.utils.mesh_export import *
from tests.common.helpers.mesh import *
from tests.utils import *


class TestMeshExportUtils(TestCase):
    def test_modifiers_are_applied_on_export(self):
        self.loadBlend(up(up(up(self.relpath()))) + '/testfiles/cube_with_modifiers.blend')

        self.assertTrue('Cube' in bpy.data.objects)

        (meshes, _)= retrieve_meshes(self, None, None, 'container_name')
      
        self.assertEqual(1, len(meshes))

        mesh = meshes[0]
        self.assertEqual(42, len(mesh.verts))

    def test_multiuser_mesh_with_modifiers_export(self):
        self.loadBlend(up(up(up(self.relpath()))) + '/testfiles/multiuser_mesh_with_modifiers.blend')

        self.assertTrue('Cube' in bpy.data.objects)
        self.assertTrue('Cube2' in bpy.data.objects)

        (meshes, _)= retrieve_meshes(self, None, None, 'container_name')
      
        self.assertEqual(2, len(meshes))

        mesh = meshes[0]
        self.assertEqual(42, len(mesh.verts))

        mesh2 = meshes[1]
        self.assertEqual(160, len(mesh2.verts))

    def test_multi_uv_vertex_splitting(self):
        mesh = bpy.data.meshes.new('mesh')

        b_mesh = bmesh.new()
        bmesh.ops.create_cube(b_mesh, size=1)
        b_mesh.to_mesh(mesh)

        tx_coords = [get_vec2(0.0, 1.0),
                     get_vec2(0.0, 0.0),
                     get_vec2(1.0, 0.0),
                     get_vec2(1.0, 1.0),
                     get_vec2(1.0, 1.0),
                     get_vec2(0.0, 1.0),
                     get_vec2(0.0, 0.0),
                     get_vec2(1.0, 0.0),
                     get_vec2(1.0, 1.0),
                     get_vec2(0.0, 1.0),
                     get_vec2(0.0, 0.0),
                     get_vec2(1.0, 0.0),
                     get_vec2(1.0, 1.0),
                     get_vec2(0.0, 1.0),
                     get_vec2(0.0, 0.0),
                     get_vec2(1.0, 0.0),
                     get_vec2(1.0, 1.0),
                     get_vec2(0.0, 1.0),
                     get_vec2(0.0, 0.0),
                     get_vec2(1.0, 0.0),
                     get_vec2(1.0, 1.0),
                     get_vec2(0.0, 1.0),
                     get_vec2(0.0, 0.0),
                     get_vec2(1.0, 0.0)]

        uv_layer = mesh.uv_layers.new(do_init=False)
        for i, datum in enumerate(uv_layer.data):
            datum.uv = tx_coords[i]

        b_mesh = prepare_bmesh(self, mesh)

        self.assertEqual(19, len(b_mesh.verts))
        self.assertEqual(12, len(b_mesh.faces))

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
