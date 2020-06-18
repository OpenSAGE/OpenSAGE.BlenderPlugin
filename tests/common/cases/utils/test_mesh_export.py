# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from os.path import dirname as up
from unittest.mock import patch
from shutil import copyfile

from io_mesh_w3d.common.utils.mesh_export import *
from io_mesh_w3d.common.utils.mesh_import import *
from io_mesh_w3d.common.utils.hierarchy_import import *
from tests.common.helpers.mesh import *
from tests.common.helpers.hierarchy import *
from tests.w3d.helpers.mesh_structs.vertex_material import *
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

    def test_retrieve_meshes_with_meshes_in_edit_mode(self):
        mesh = get_mesh()
        create_mesh(self, mesh, get_collection())

        meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        for mesh_ob in meshes:
            if mesh_ob.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

        meshes, _ = retrieve_meshes(self, None, None, 'containerName')

        compare_meshes(self, mesh, meshes[0])

    def test_retrieve_meshes_with_bone_weights_are_zero(self):
        coll = get_collection()
        mesh = get_mesh(skin=True)
        create_mesh(self, mesh, coll)

        hierarchy = get_hierarchy()
        rig = get_or_create_skeleton(hierarchy, coll)

        rig_mesh(mesh, hierarchy, rig)

        meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        for mesh_object in meshes:
            for i, vertex in enumerate(mesh_object.data.vertices):
                if vertex.groups:
                    vertex.groups[0].weight = 0.0
                    if len(vertex.groups) > 1:
                        vertex.groups[1].weight = 0.0

        for inf in mesh.vert_infs:
            inf.bone_inf = 1.0
            inf.xtra_inf = 0.0

        meshes, _ = retrieve_meshes(self, hierarchy, rig, 'containerName')

        compare_meshes(self, mesh, meshes[0])

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

    def test_mesh_export_W3X_too_few_uv_layers(self):
        self.file_format = 'W3X'
        mesh = bpy.data.meshes.new('mesh_cube')

        b_mesh = bmesh.new()
        bmesh.ops.create_cube(b_mesh, size=1)
        b_mesh.to_mesh(mesh)

        material = bpy.data.materials.new('material')
        mesh.materials.append(material)

        mesh_ob = bpy.data.objects.new('mesh_object', mesh)
        mesh_ob.object_type = 'NORMAL'

        coll = bpy.context.scene.collection
        coll.objects.link(mesh_ob)
        bpy.context.view_layer.objects.active = mesh_ob
        mesh_ob.select_set(True)

        meshes, _ = retrieve_meshes(self, None, None, 'container_name')

        self.assertEqual(0, len(meshes[0].material_passes[0].tx_coords))

    def test_mesh_export_W3D_too_few_uv_layers(self):
        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds', self.outpath() + 'texture.dds')
        self.file_format = 'W3D'
        mesh = bpy.data.meshes.new('mesh_cube')

        b_mesh = bmesh.new()
        bmesh.ops.create_cube(b_mesh, size=1)
        b_mesh.to_mesh(mesh)

        material, principled = create_material_from_vertex_material('loem ipsum', get_vertex_material())
        tex = find_texture(self, 'texture.dds')
        principled.base_color_texture.image = tex
        mesh.materials.append(material)

        mesh_ob = bpy.data.objects.new('mesh_object', mesh)
        mesh_ob.object_type = 'NORMAL'

        coll = bpy.context.scene.collection
        coll.objects.link(mesh_ob)
        bpy.context.view_layer.objects.active = mesh_ob
        mesh_ob.select_set(True)

        meshes, _ = retrieve_meshes(self, None, None, 'container_name')

        self.assertEqual(0, len(meshes[0].material_passes[0].tx_stages))
