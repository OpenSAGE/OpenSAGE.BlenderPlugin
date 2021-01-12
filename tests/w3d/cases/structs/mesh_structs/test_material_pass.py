# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.utils import TestCase
from tests.w3d.helpers.mesh_structs.material_pass import *


class TestMaterialPass(TestCase):
    def test_write_read(self):
        expected = get_material_pass()

        self.assertEqual(348, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = MaterialPass.read(self, io_stream, chunkEnd)
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

        actual = MaterialPass.read(self, io_stream, chunkEnd)
        compare_material_passes(self, expected, actual)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_MATERIAL_PASS,
                         output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunk_type)

        self.warning = lambda text: self.assertEqual('unknown chunk_type in io_stream: 0x0', text)
        MaterialPass.read(self, io_stream, subchunk_end)

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


class TestTextureStage(TestCase):
    def test_write_read(self):
        expected = get_texture_stage()

        self.assertEqual(196, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = TextureStage.read(self, io_stream, chunkEnd)
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

        actual = TextureStage.read(self, io_stream, chunkEnd)
        compare_texture_stages(self, expected, actual)

    def test_unsupported_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_TEXTURE_STAGE,
                         output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunk_type)

        TextureStage.read(self, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        stage = get_texture_stage_minimal()

        self.assertEqual(4, long_list_size(stage.tx_ids, False))

        self.assertEqual(12, vec_list_size(stage.per_face_tx_coords, False))

        self.assertEqual(8, vec2_list_size(stage.tx_coords, False))

        self.assertEqual(48, stage.size(False))
        self.assertEqual(56, stage.size())
