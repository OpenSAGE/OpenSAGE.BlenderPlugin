# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from shutil import copyfile

from io_mesh_w3d.import_utils import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import *
from tests.utils import *
from tests.w3d.helpers.compressed_animation import *
from tests.w3d.helpers.mesh_structs.material_pass import *
from os.path import dirname as up


class TestImportUtilsW3D(TestCase):
    def test_material_pass_with_2_texture_stages(self):
        mesh_struct = get_mesh()
        triangles = []

        for triangle in mesh_struct.triangles:
            triangles.append(triangle.vert_ids)

        verts = mesh_struct.verts.copy()
        mesh = bpy.data.meshes.new(mesh_struct.header.mesh_name)
        mesh.from_pydata(verts, [], triangles)
        mesh.update()
        mesh.validate()
        b_mesh = bmesh.new()
        b_mesh.from_mesh(mesh)

        mesh_struct.material_passes[0].tx_stages.append(get_texture_stage())

        for mat_pass in mesh_struct.material_passes:
            create_uvlayer(self, mesh, b_mesh, triangles, mat_pass)

    def test_mesh_import_2_textures_1_vertex_material(self):
        mesh = get_mesh_two_textures()

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')
        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture2.dds')

        create_mesh(self, mesh, bpy.context.collection)

    def test_prelit_mesh_import(self):
        mesh = get_mesh(prelit=True)

        create_mesh(self, mesh, bpy.context.collection)

    def test_duplicate_vertex_material_creation(self):
        vert_mats = [get_vertex_material(vm_name='VM_NAME'), get_vertex_material(vm_name='VM_NAME')]

        for mat in vert_mats:
            create_material_from_vertex_material('meshName', mat)

        self.assertEqual(1, len(bpy.data.materials))
        self.assertTrue('meshName.VM_NAME' in bpy.data.materials)

    def test_deduplicate_materials_merges_identical_materials_from_different_meshes(self):
        mat_a, _ = create_material_from_vertex_material('mesh1', get_vertex_material())
        mat_b, _ = create_material_from_vertex_material('mesh2', get_vertex_material())

        self.assertEqual(2, len(bpy.data.materials))
        self.assertNotEqual(mat_a, mat_b)

        merged = deduplicate_materials([mat_a, mat_b])

        self.assertEqual(1, merged)
        self.assertEqual(1, len(bpy.data.materials))
        self.assertTrue('mesh1.VM_NAME' in bpy.data.materials)
        self.assertFalse('mesh2.VM_NAME' in bpy.data.materials)

    def test_deduplicate_materials_ignores_foreign_addon_properties(self):
        # simulates a third-party addon (e.g. BlenderKit) registering its own custom
        # runtime property on Material; such properties must not block deduplication,
        # even when their values differ between the two materials being compared
        bpy.types.Material.foreign_addon_prop = bpy.props.StringProperty(default='')
        try:
            mat_a, _ = create_material_from_vertex_material('mesh1', get_vertex_material())
            mat_b, _ = create_material_from_vertex_material('mesh2', get_vertex_material())
            mat_a.foreign_addon_prop = 'a'
            mat_b.foreign_addon_prop = 'b'

            merged = deduplicate_materials([mat_a, mat_b])

            self.assertEqual(1, merged)
            self.assertEqual(1, len(bpy.data.materials))
        finally:
            del bpy.types.Material.foreign_addon_prop

    def test_deduplicate_materials_keeps_differing_materials_separate(self):
        vm_b = get_vertex_material()
        vm_b.vm_info.diffuse.r = 250

        mat_a, _ = create_material_from_vertex_material('mesh1', get_vertex_material())
        mat_b, _ = create_material_from_vertex_material('mesh2', vm_b)

        merged = deduplicate_materials([mat_a, mat_b])

        self.assertEqual(0, merged)
        self.assertEqual(2, len(bpy.data.materials))

    def test_deduplicate_materials_redirects_mesh_slots_to_the_canonical_material(self):
        mat_a, _ = create_material_from_vertex_material('mesh1', get_vertex_material())
        mat_b, _ = create_material_from_vertex_material('mesh2', get_vertex_material())

        mesh = bpy.data.meshes.new('probe')
        mesh.materials.append(mat_b)

        deduplicate_materials([mat_a, mat_b])

        self.assertEqual(mat_a, mesh.materials[0])

    def test_meshes_sharing_a_material_definition_share_one_material_on_import(self):
        meshes = [get_mesh(name='mesh1', mat_count=1), get_mesh(name='mesh2', mat_count=1)]

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds', self.outpath() + 'texture.dds')

        create_data(self, meshes)

        mesh1 = bpy.data.objects['mesh1'].data
        mesh2 = bpy.data.objects['mesh2'].data

        self.assertEqual(1, len(mesh1.materials))
        self.assertEqual(1, len(mesh2.materials))
        self.assertEqual(mesh1.materials[0], mesh2.materials[0])

    def test_only_needed_keyframe_creation(self):
        animation = get_compressed_animation_empty()

        channel = TimeCodedAnimationChannel(
            num_time_codes=5,
            pivot=1,
            type=1,
            time_codes=[TimeCodedDatum(time_code=0, value=3.0),
                        TimeCodedDatum(time_code=1, value=3.0),
                        TimeCodedDatum(time_code=2, value=3.0),
                        TimeCodedDatum(time_code=3, value=3.0),
                        TimeCodedDatum(time_code=4, value=3.0)])
        animation.time_coded_channels = [channel]

        hlod = get_hlod()
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=1, name='containerName.MESH')]

        hierarchy = get_hierarchy()
        pivot = HierarchyPivot(
            name='MESH',
            parent_id=0)

        hierarchy.pivots = [get_roottransform(), pivot]

        meshes = [get_mesh(name='MESH_Obj')]

        expected_frames = [0, 4]
        if bpy.app.version >= (4, 2, 0):
            expected_frames = [0]
        expected = [3.0, 3.0]

        self.filepath = self.outpath() + 'output'
        create_data(self, meshes, hlod, hierarchy, [], None, animation)

        obj = bpy.data.objects['TestHierarchy']
        for fcu in iter_action_fcurves(obj.animation_data):
            self.assertEqual(len(expected_frames), len(fcu.keyframe_points))
            for i, keyframe in enumerate(fcu.keyframe_points):
                frame = int(keyframe.co.x)
                self.assertEqual(expected_frames[i], frame)
                val = keyframe.co.y
                self.assertEqual(expected[i], val)
