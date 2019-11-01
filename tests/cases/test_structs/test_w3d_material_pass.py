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

        self.assertEqual(348, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = MaterialPass.read(io_stream, chunkEnd)
        compare_material_passes(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_material_pass_empty()

        self.assertEqual(8, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = MaterialPass.read(io_stream, chunkEnd)
        compare_material_passes(self, expected, actual)

    def test_chunk_sizes(self):
        expected = get_material_pass_minimal()

        self.assertEqual(4, expected.vertex_material_ids_size(False))
        self.assertEqual(12, expected.vertex_material_ids_size())

        self.assertEqual(4, expected.shader_ids_size(False))
        self.assertEqual(12, expected.shader_ids_size())

        self.assertEqual(4, expected.dcg_size(False))
        self.assertEqual(12, expected.dcg_size())

        self.assertEqual(4, expected.dig_size(False))
        self.assertEqual(12, expected.dig_size())

        self.assertEqual(4, expected.scg_size(False))
        self.assertEqual(12, expected.scg_size())

        self.assertEqual(4, expected.shader_material_ids_size(False))
        self.assertEqual(12, expected.shader_material_ids_size())

        self.assertEqual(196, expected.tx_stages_size())

        self.assertEqual(284, expected.size(False))
        self.assertEqual(292, expected.size())



class TestTextureStage(unittest.TestCase):
    def test_write_read(self):
        expected = get_texture_stage()

        self.assertEqual(196, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = TextureStage.read(io_stream, chunkEnd)
        compare_texture_stages(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_texture_stage_empty()

        self.assertEqual(8, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = TextureStage.read(io_stream, chunkEnd)
        compare_texture_stages(self, expected, actual)

    def test_chunk_sizes(self):
        expected = get_texture_stage_minimal()

        self.assertEqual(4, expected.tx_ids_size(False))
        self.assertEqual(12, expected.tx_ids_size())

        self.assertEqual(12, expected.per_face_tx_coords_size(False))
        self.assertEqual(20, expected.per_face_tx_coords_size())

        self.assertEqual(8, expected.tx_coords_size(False))
        self.assertEqual(16, expected.tx_coords_size())

        self.assertEqual(48, expected.size(False))
        self.assertEqual(56, expected.size())