# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from os.path import dirname as up
from unittest.mock import patch

from io_mesh_w3d.common.utils.mesh_export import *
from io_mesh_w3d.common.utils.mesh_import import *
from tests.common.helpers.mesh import *
from tests.utils import *


class TestMeshExportUtils(TestCase):
    def test_modifiers_are_applied_on_export(self):
        self.loadBlend(up(up(up(self.relpath()))) + '/testfiles/cube_with_modifiers.blend')

        self.assertTrue('Cube' in bpy.data.objects)

        meshes, _ = retrieve_meshes(self, None, None, 'container_name')

        self.assertEqual(1, len(meshes))

        mesh = meshes[0]
        self.assertEqual(42, len(mesh.verts))

    def test_multiuser_mesh_with_modifiers_export(self):
        self.loadBlend(up(up(up(self.relpath()))) + '/testfiles/multiuser_mesh_with_modifiers.blend')

        self.assertTrue('Cube' in bpy.data.objects)
        self.assertTrue('Cube2' in bpy.data.objects)

        meshes, _ = retrieve_meshes(self, None, None, 'container_name')

        self.assertEqual(2, len(meshes))

        mesh = meshes[0]
        self.assertEqual(42, len(mesh.verts))

        mesh2 = meshes[1]
        self.assertEqual(34, len(mesh2.verts))

    def test_trianglulation_of_sphere(self):
        mesh = bpy.data.meshes.new('sphere')
        sphere = bpy.data.objects.new('sphere', mesh)

        b_mesh = bmesh.new()
        bmesh.ops.create_uvsphere(b_mesh, u_segments=12, v_segments=6, diameter=35)
        b_mesh.to_mesh(mesh)
        b_mesh.free()

        coll = get_collection()
        coll.objects.link(sphere)

        meshes, _ = retrieve_meshes(self, None, None, 'container_name')

        self.assertEqual(62, len(meshes[0].verts))
        self.assertEqual(120, len(meshes[0].triangles))

    def test_used_texture_file_ending_is_correct(self):
        create_mesh(self, get_mesh(), get_collection())

        meshes, _ = retrieve_meshes(self, None, None, 'container_name')

        mesh = meshes[0]
        self.assertEqual(mesh.textures[0].file, 'texture.dds')
        self.assertEqual(mesh.textures[1].file, 'texture.dds')

    def test_user_is_notified_if_a_material_of_the_mesh_is_none(self):
        mesh = get_mesh('mesh')
        mesh.textures = []
        mesh.material_passes[0].tx_stages = []
        mesh.material_passes[1].tx_stages = []
        create_mesh(self, mesh, get_collection())

        mesh_structs, textures = retrieve_meshes(self, None, None, 'container_name')
        self.assertEqual(0, len(mesh_structs[0].material_passes[0].tx_stages))

    def test_material_pass_does_not_contain_texture_stages_if_no_texture_is_applied(self):
        create_mesh(self, get_mesh('mesh'), get_collection())

        mesh = bpy.data.objects['mesh']
        mesh.data.materials.append(None)

        with (patch.object(self, 'warning')) as warning_func:
            retrieve_meshes(self, None, None, 'container_name')
            warning_func.assert_called_with('mesh \'mesh\' uses a invalid/empty material!')

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

        _mesh = prepare_bmesh(self, mesh)

        self.assertEqual(24, len(_mesh.verts))
        self.assertEqual(12, len(_mesh.faces))

    def test_mesh_with_unconnected_vertex_export(self):
        mesh = bpy.data.meshes.new('mesh_cube')

        material = bpy.data.materials.new('material')
        mesh.materials.append(material)

        b_mesh = bmesh.new()
        bmesh.ops.create_cube(b_mesh, size=1)
        b_mesh.verts.new((9, 9, 9))
        bmesh.ops.triangulate(b_mesh, faces=b_mesh.faces)
        b_mesh.to_mesh(mesh)
        mesh.uv_layers.new(do_init=False)

        mesh_ob = bpy.data.objects.new('mesh_object', mesh)
        mesh_ob.object_type = 'NORMAL'

        coll = bpy.context.scene.collection
        coll.objects.link(mesh_ob)
        bpy.context.view_layer.objects.active = mesh_ob
        mesh_ob.select_set(True)

        meshes, _ = retrieve_meshes(self, None, None, 'container_name')

        io_stream = io.BytesIO()
        for mesh_struct in meshes:
            mesh_struct.write(io_stream)

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
