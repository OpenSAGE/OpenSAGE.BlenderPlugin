# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import read_chunk_head
from tests.helpers.w3d_material_pass import *


class TestMaterialPass(unittest.TestCase):
    def test_write_read(self):
        expected = get_material_pass()

        self.assertEqual(340, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = MaterialPass.read(io_stream, chunkEnd)
        compare_material_passes(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_material_pass(minimal=True)

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

        self.assertEqual(188, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = TextureStage.read(io_stream, chunkEnd)
        compare_texture_stages(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_texture_stage(minimal=True)

        self.assertEqual(0, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = TextureStage.read(io_stream, chunkEnd)
        compare_texture_stages(self, expected, actual)