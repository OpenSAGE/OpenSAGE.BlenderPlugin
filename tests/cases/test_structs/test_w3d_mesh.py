# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 11.2019
import unittest
import io
from tests import utils

from io_mesh_w3d.structs.w3d_mesh import *
from io_mesh_w3d.io_binary import read_chunk_head, write_chunk_head, write_ubyte

from tests.helpers.w3d_mesh import *


class TestMesh(utils.W3dTestCase):
    def test_write_read(self):
        expected = get_mesh()

        self.assertEqual(3113, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)
        compare_meshes(self, expected, actual)

    def test_write_read_variant2(self):
        expected = get_mesh(skin=True, shader_mats=True)

        self.assertEqual(3601, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)
        compare_meshes(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_mesh_empty()

        self.assertEqual(204, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)
        compare_meshes(self, expected, actual)

    def test_chunk_order(self):
        expected_chunks = [
            W3D_CHUNK_MESH_HEADER,
            W3D_CHUNK_MESH_USER_TEXT,
            W3D_CHUNK_VERTICES,
            # vertices copies not used
            W3D_CHUNK_VERTEX_NORMALS,
            # normals copies not used
            W3D_CHUNK_TRIANGLES,
            W3D_CHUNK_VERTEX_INFLUENCES,
            W3D_CHUNK_VERTEX_SHADE_INDICES,
            W3D_CHUNK_MATERIAL_INFO,
            W3D_CHUNK_VERTEX_MATERIALS,
            W3D_CHUNK_SHADERS,
            W3D_CHUNK_TEXTURES,
            W3D_CHUNK_SHADER_MATERIALS,
            W3D_CHUNK_MATERIAL_PASS
        ]

        expected = get_mesh()
        expected.vert_infs = get_vertex_influences()
        expected.shader_materials = [get_shader_material()]
        expected.shaders = [get_shader()]
        expected.vert_materials = [get_vertex_material()]
        expected.textures = [get_texture()]
        expected.material_passes = [get_material_pass()]

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size(), chunk_size)

        for chunk in expected_chunks:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)
            self.assertEqual(hex(chunk), hex(chunk_type))
            io_stream.seek(chunk_size, 1)

    def test_unsupported_chunk_skip(self):
        context = utils.ImportWrapper(self.outpath())
        output = io.BytesIO()
        write_chunk_head(output, W3D_CHUNK_MESH, 99, has_sub_chunks=True)

        write_chunk_head(output, W3D_CHUNK_VERTICES_2, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_NORMALS_2, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_TANGENTS, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_BITANGENTS, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_PRELIT_UNLIT,
                         1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_PRELIT_VERTEX,
                         1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(
            output,
            W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS,
            1,
            has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(
            output,
            W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE,
            1,
            has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_DEFORM, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_PS2_SHADERS,
                         1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, 0, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)

        io_stream = io.BytesIO(output.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)

        Mesh.read(context, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        mesh = get_mesh_minimal()

        self.assertEqual(116, mesh.header.size(False))
        self.assertEqual(124, mesh.header.size())

        self.assertEqual(5, mesh.user_text_size(False))
        self.assertEqual(13, mesh.user_text_size())

        self.assertEqual(12, mesh.verts_size(False))
        self.assertEqual(20, mesh.verts_size())

        self.assertEqual(12, mesh.normals_size(False))
        self.assertEqual(20, mesh.normals_size())

        self.assertEqual(32, mesh.tris_size(False))
        self.assertEqual(40, mesh.tris_size())

        self.assertEqual(16, mesh.shaders_size(False))
        self.assertEqual(24, mesh.shaders_size())

        self.assertEqual(38, mesh.textures_size(False))
        self.assertEqual(46, mesh.textures_size())

        self.assertEqual(4, mesh.shade_ids_size(False))
        self.assertEqual(12, mesh.shade_ids_size())

        self.assertEqual(240, mesh.shader_materials_size(False))
        self.assertEqual(248, mesh.shader_materials_size())

        self.assertEqual(292, mesh.material_passes_size())

        self.assertEqual(78, mesh.vert_materials_size(False))
        self.assertEqual(86, mesh.vert_materials_size())

        self.assertEqual(1041, mesh.size())
