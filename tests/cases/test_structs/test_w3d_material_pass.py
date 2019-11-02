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

    def test_write_read_empty(self):
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
        mpass = get_material_pass_minimal()

        self.assertEqual(4, long_list_size(mpass.vertex_material_ids, False))

        self.assertEqual(4, long_list_size(mpass.shader_ids, False))

        self.assertEqual(4, list_size(mpass.dcg, False))
        self.assertEqual(4, list_size(mpass.dig, False))
        self.assertEqual(4, list_size(mpass.scg, False))

        self.assertEqual(4, long_list_size(mpass.shader_material_ids, False))

        self.assertEqual(196, list_size(mpass.tx_stages, False))

        self.assertEqual(284, mpass.size(False))
        self.assertEqual(292, mpass.size())



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

    def test_write_read_empty(self):
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
        stage = get_texture_stage_minimal()

        self.assertEqual(4, long_list_size(stage.tx_ids, False))

        self.assertEqual(12, vec_list_size(stage.per_face_tx_coords, False))

        self.assertEqual(8, vec2_list_size(stage.tx_coords, False))

        self.assertEqual(48, stage.size(False))
        self.assertEqual(56, stage.size())