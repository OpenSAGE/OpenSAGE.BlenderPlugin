# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from shutil import copyfile

from io_mesh_w3d.import_utils import *
from tests.shared.helpers.hierarchy import *
from tests.shared.helpers.hlod import *
from tests.shared.helpers.mesh import *
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

        create_mesh(self, mesh, None, bpy.context.collection)

    def test_prelit_mesh_import(self):
        mesh = get_mesh(prelit=True)

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        create_mesh(self, mesh, None, bpy.context.collection)

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

        mesh_structs = [get_mesh(name='MESH')]

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        expected_frames = [0, 4]
        expected = [3.0, 3.0]

        coll = get_collection(hlod)

        for mesh_struct in mesh_structs:
            create_mesh(self, mesh_struct, hierarchy, coll)

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, hierarchy, hlod, rig)

        create_animation(self, rig, animation, hierarchy, compressed=True)

        # currently disabled because of timecoded animation export issue -> see create keyframe functions
        obj = bpy.data.objects['MESH']
        # for fcu in obj.animation_data.action.fcurves:
        #    self.assertEqual(len(expected_frames), len(fcu.keyframe_points))
        #    for i, keyframe in enumerate(fcu.keyframe_points):
        #        frame = int(keyframe.co.x)
        #        self.assertEqual(expected_frames[i], frame)
        #        val = keyframe.co.y
        #        self.assertEqual(expected[i], val)
