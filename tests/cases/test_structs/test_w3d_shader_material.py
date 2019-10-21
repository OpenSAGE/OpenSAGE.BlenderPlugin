# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_shader_material import ShaderMaterial, ShaderMaterialHeader, \
    ShaderMaterialProperty, W3D_CHUNK_SHADER_MATERIAL
from io_mesh_w3d.io_binary import read_chunk_head
from tests.helpers.w3d_shader_material import get_shader_material, compare_shader_materials


class TestShaderMaterial(unittest.TestCase):
    def test_write_read(self):
        expected = get_shader_material()

        self.assertEqual(37, expected.header.size_in_bytes())
        self.assertEqual(370, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = ShaderMaterial.read(self, io_stream, chunkEnd)
        compare_shader_materials(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_shader_material(props=[])

        self.assertEqual(37, expected.header.size_in_bytes())
        self.assertEqual(45, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = ShaderMaterial.read(self, io_stream, chunkEnd)
        compare_shader_materials(self, expected, actual)

