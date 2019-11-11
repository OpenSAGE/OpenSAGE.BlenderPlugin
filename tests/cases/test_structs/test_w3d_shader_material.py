# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from tests import utils

from io_mesh_w3d.structs.w3d_shader_material import *
from io_mesh_w3d.io_binary import *
from tests.helpers.w3d_shader_material import *


class TestShaderMaterial(utils.W3dTestCase):
    def test_write_read(self):
        expected = get_shader_material()

        self.assertEqual(45, expected.header.size())
        self.assertEqual(502, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = ShaderMaterial.read(self, io_stream, chunkEnd)
        compare_shader_materials(self, expected, actual)

    def test_write_read_empty(self):
        expected = get_shader_material_empty()

        self.assertEqual(45, expected.header.size())
        self.assertEqual(53, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = ShaderMaterial.read(self, io_stream, chunkEnd)
        compare_shader_materials(self, expected, actual)

    def test_unknown_chunk_skip(self):
        context = utils.ImportWrapper(self.outpath())
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL, chunk_type)

        ShaderMaterial.read(context, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        material = get_shader_material_minimal()

        self.assertEqual(37, material.header.size(False))
        self.assertEqual(45, material.header.size())

        prop_1 = material.properties[0]
        self.assertEqual(26, prop_1.size(False))
        self.assertEqual(34, prop_1.size())

        prop_2 = material.properties[1]
        self.assertEqual(14, prop_2.size(False))
        self.assertEqual(22, prop_2.size())

        prop_3 = material.properties[2]
        self.assertEqual(18, prop_3.size(False))
        self.assertEqual(26, prop_3.size())

        prop_4 = material.properties[3]
        self.assertEqual(22, prop_4.size(False))
        self.assertEqual(30, prop_4.size())

        prop_5 = material.properties[4]
        self.assertEqual(26, prop_5.size(False))
        self.assertEqual(34, prop_5.size())

        prop_6 = material.properties[5]
        self.assertEqual(14, prop_6.size(False))
        self.assertEqual(22, prop_6.size())

        prop_7 = material.properties[6]
        self.assertEqual(11, prop_7.size(False))
        self.assertEqual(19, prop_7.size())

        self.assertEqual(232, material.size(False))
        self.assertEqual(240, material.size())
