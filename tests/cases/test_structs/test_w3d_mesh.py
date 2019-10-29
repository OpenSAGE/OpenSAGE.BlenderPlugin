# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io
from tests import utils

from io_mesh_w3d.structs.w3d_mesh import *
from io_mesh_w3d.io_binary import read_chunk_head, write_chunk_head, write_ubyte

from tests.helpers.w3d_mesh import get_mesh, compare_meshes

class TestMesh(utils.W3dTestCase):
    def test_write_read(self):
        expected = get_mesh()

        self.assertEqual(3113, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size_in_bytes(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)
        compare_meshes(self, expected, actual)


    def test_write_read_variant2(self):
        expected = get_mesh(skin=True, shader_mats=True)

        self.assertEqual(3353, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size_in_bytes(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)
        compare_meshes(self, expected, actual)


    def test_write_read_minimal(self):
        expected = get_mesh(minimal=True)

        self.assertEqual(148, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size_in_bytes(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)
        compare_meshes(self, expected, actual)


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
        write_chunk_head(output, W3D_CHUNK_PRELIT_UNLIT, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_PRELIT_VERTEX, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_DEFORM, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, W3D_CHUNK_PS2_SHADERS, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)
        write_chunk_head(output, 0, 1, has_sub_chunks=False)
        write_ubyte(output, 0x00)

        io_stream = io.BytesIO(output.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)

        Mesh.read(context, io_stream, subchunk_end)