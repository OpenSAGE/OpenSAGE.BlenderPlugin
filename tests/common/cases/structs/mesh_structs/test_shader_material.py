# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.mesh_structs.shader_material import *
from tests.utils import TestCase


class TestShaderMaterial(TestCase):
    def test_write_read(self):
        expected = get_shader_material()

        self.assertEqual(45, expected.header.size())
        self.assertEqual(1544, expected.size())

        self.write_read_test(expected, W3D_CHUNK_SHADER_MATERIAL, ShaderMaterial.read,
                             compare_shader_materials, self, True)

    def test_read_invalid_property(self):
        io_stream = io.BytesIO()

        name = 'InvalidProp'
        size = 8 + len(name) + 1 + 1
        type = 0

        write_chunk_head(
            W3D_CHUNK_SHADER_MATERIAL_PROPERTY, io_stream, size)
        write_long(type, io_stream)
        write_long(len(name) + 1, io_stream)
        write_string(name, io_stream)
        write_ubyte(0x00, io_stream)  # fake data

        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL_PROPERTY, chunkType)
        self.assertEqual(size, chunkSize)

        ShaderMaterialProperty.read(self, io_stream)

    def test_write_invalid_property(self):
        io_stream = io.BytesIO()

        prop = ShaderMaterialProperty(
            type=0,
            name='InvalidProp',
            value=0x00)

        prop.write(io_stream)

        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL_PROPERTY, chunkType)
        self.assertEqual(prop.size(False), chunkSize)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL, chunk_type)

        self.warning = lambda text: self.assertEqual('unknown chunk_type in io_stream: 0x0', text)
        ShaderMaterial.read(self, io_stream, subchunk_end)

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

    def test_write_read_xml(self):
        self.write_read_xml_test(
            get_shader_material(),
            'FXShader',
            ShaderMaterial.parse,
            compare_shader_materials)

    def test_write_read_rgb_colors_xml(self):
        self.write_read_xml_test(
            get_shader_material(rgb_colors=True),
            'FXShader',
            ShaderMaterial.parse,
            compare_shader_materials)

    def test_write_read_xml_no_technique_index(self):
        expected = get_shader_material_minimal()
        expected.header.technique_index = 0
        self.write_read_xml_test(expected, 'FXShader', ShaderMaterial.parse, compare_shader_materials)

    def test_write_read_xml_bool_is_written_lowercase(self):
        expected = get_shader_material_minimal()

        root = create_root()
        expected.create(root)

        for child in root.find('FXShader'):
            if child.tag != 'Constants':
                continue
            for prop in child:
                if prop.tag == 'Bool':
                    value = prop.find('Value').text
                    self.assertTrue(value in ['true', 'false'])
