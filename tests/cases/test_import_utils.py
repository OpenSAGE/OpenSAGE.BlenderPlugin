# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests import utils
from shutil import copyfile

from io_mesh_w3d.import_utils_w3d import *
from tests.helpers.w3d_mesh import *
from tests.helpers.w3d_material_pass import *


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
        read_chunk_array(context, io_stream, 27, W3D_CHUNK_MATERIAL_PASS, MaterialPass.read)