# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from shutil import copyfile
from tests.utils import TestCase
from io_mesh_w3d.import_utils_w3d import *
from tests.helpers.w3d_mesh import *
from tests.helpers.w3d_material_pass import *
from tests.helpers.w3d_hlod import *
from tests.helpers.w3d_hierarchy import *
from tests.helpers.w3d_animation import *
from tests.helpers.w3d_compressed_animation import *


class TestImportUtils(TestCase):
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
            create_uvlayer(mesh, b_mesh, triangles, mat_pass)

    def test_mesh_import_2_textures_1_vertex_material(self):
        mesh = get_mesh_two_textures()

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture2.dds")

        create_mesh(self, mesh, None, bpy.context.collection)


    def test_prelit_mesh_import(self):
        mesh = get_mesh(prelit = True)

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_mesh(self, mesh, None, bpy.context.collection)


    def test_parent_is_none_if_parent_index_is_0_or_less_than_0(self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()

        root = get_hierarchy_pivot("ROOTTRANSFORM", -1)
        root.translation = Vector()
        root.rotation = Quaternion()
        root.euler_angles = Vector((0.0, 0.0, 0.0))

        hierarchy.pivots = [root]

        hierarchy.pivots.append(get_hierarchy_pivot("first", 0))
        hierarchy.pivots.append(get_hierarchy_pivot("second", -1))

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodArray(
            header=get_hlod_array_header(),
            sub_objects=[])

        array.sub_objects.append(get_hlod_sub_object(
            bone=1, name="containerName.first"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=2, name="containerName.second"))

        array.header.model_count = len(array.sub_objects)

        hlod.lod_array = array

        mesh_structs = [
            get_mesh(name="first"),
            get_mesh(name="second")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        self.assertTrue("first" in bpy.data.objects)
        first = bpy.data.objects["first"]
        self.assertIsNone(first.parent)

        self.assertTrue("second" in bpy.data.objects)
        second = bpy.data.objects["second"]
        self.assertIsNone(second.parent)

    def test_read_chunk_array(self):
        output = io.BytesIO()

        mat_pass = get_material_pass()
        mat_pass.write(output)
        mat_pass.write(output)
        mat_pass.write(output)

        write_chunk_head(0x00, output, 9, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        read_chunk_array(self, io_stream, mat_pass.size()
                         * 3 + 9, W3D_CHUNK_MATERIAL_PASS, MaterialPass.read)

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
        hlod.lod_array.sub_objects = [
            get_hlod_sub_object(bone=1, name="containerName.MESH")]

        hierarchy = get_hierarchy()
        pivot = HierarchyPivot(
            name="mesh",
            parent_id=0)

        hierarchy.pivots = [get_roottransform(), pivot]

        mesh_structs = [get_mesh(name="mesh")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        expected_frames = [0, 4]
        expected = [3.0, 3.0]

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        create_animation(rig, animation, hierarchy, compressed=True)

        obj = bpy.data.objects['mesh']
        for fcu in obj.animation_data.action.fcurves:
            self.assertEqual(len(expected_frames), len(fcu.keyframe_points))
            for i, keyframe in enumerate(fcu.keyframe_points):
                frame = int(keyframe.co.x)
                self.assertEqual(expected_frames[i], frame)
                val = keyframe.co.y
                self.assertEqual(expected[i], val)
