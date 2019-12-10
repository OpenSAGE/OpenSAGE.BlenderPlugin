# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests import utils
from shutil import copyfile

from io_mesh_w3d.import_utils_w3d import *
from tests.helpers.w3d_mesh import *
from tests.helpers.w3d_material_pass import *
from tests.helpers.w3d_hlod import * 
from tests.helpers.w3d_hierarchy import *


class TestImportUtils(utils.W3dTestCase):
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
        context = utils.ImportWrapper(self.outpath())
        mesh = get_mesh_two_textures()

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")
        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture2.dds")

        create_mesh(context, mesh, None, bpy.context.collection)


    def test_parent_is_none_if_parent_index_is_0_or_less_than_0(self):
        context = utils.ImportWrapper(self.outpath())
        hlod = get_hlod()
        hierarchy = get_hierarchy()

        root = get_hierarchy_pivot("ROOTTRANSFORM", -1)
        root.translation = Vector()
        root.rotation = Quaternion()
        root.euler_angles = Vector((0.0, 0.0, 0.0))

        hierarchy.pivots= [root]

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
            meshes.append(create_mesh(context, mesh_struct, hierarchy, coll))

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
        context = utils.ImportWrapper(self.outpath())
        output = io.BytesIO()

        mat_pass = get_material_pass()
        mat_pass.write(output)
        mat_pass.write(output)
        mat_pass.write(output)

        write_chunk_head(0x00, output, 9, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        read_chunk_array(context, io_stream, mat_pass.size()
                         * 3 + 9, W3D_CHUNK_MATERIAL_PASS, MaterialPass.read)
