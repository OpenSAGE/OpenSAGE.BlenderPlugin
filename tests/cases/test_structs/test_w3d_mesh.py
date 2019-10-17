# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_mesh import Mesh, W3D_CHUNK_MESH
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_mesh import get_mesh, compare_meshes

class TestMesh(unittest.TestCase):
    def test_write_read(self):
        expected = get_mesh()

        self.assertEqual(39099, expected.size_in_bytes())

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