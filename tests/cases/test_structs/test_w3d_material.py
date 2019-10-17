# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_material import VertexMaterial, VertexMaterialInfo, \
    MaterialInfo, MaterialPass, TextureStage, W3D_CHUNK_VERTEX_MATERIAL, \
    W3D_CHUNK_MATERIAL_PASS, W3D_CHUNK_TEXTURE_STAGE
from io_mesh_w3d.io_binary import read_chunk_head

from tests.helpers.w3d_material import get_vertex_material, compare_vertex_materials, \
    get_material_pass, compare_material_passes, compare_texture_stages, get_material_info, \
    get_texture_stage, compare_material_infos, compare_texture_stages


class TestVertexMaterial(unittest.TestCase):
    def test_write_read(self):
        expected = get_vertex_material()

        self.assertEqual(32, expected.vm_info.size_in_bytes())
        self.assertEqual(90, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_VERTEX_MATERIAL, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = VertexMaterial.read(self, io_stream, chunkEnd)
        compare_vertex_materials(self, expected, actual)


class TestMaterialInfo(unittest.TestCase):
    def test_write_read(self):
        expected = get_material_info()

        self.assertEqual(16, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = MaterialInfo.read(io_stream)

        compare_material_infos(self, expected, actual)


class TestMaterialPass(unittest.TestCase):
    def test_write_read(self):
        expected = get_material_pass()

        self.assertEqual(7080, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = MaterialPass.read(io_stream, chunkEnd)
        compare_material_passes(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_material_pass(count=0, num_stages=0)

        self.assertEqual(0, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = MaterialPass.read(io_stream, chunkEnd)
        compare_material_passes(self, expected, actual)


class TestTextureStage(unittest.TestCase):
    def test_write_read(self):
        expected = get_texture_stage()

        self.assertEqual(2976, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = TextureStage.read(io_stream, chunkEnd)
        compare_texture_stages(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_texture_stage(0)

        self.assertEqual(0, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = TextureStage.read(io_stream, chunkEnd)
        compare_texture_stages(self, expected, actual)