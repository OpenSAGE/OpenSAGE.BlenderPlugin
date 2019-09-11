# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_shader_material import ShaderMaterial, ShaderMaterialHeader, \
    ShaderMaterialProperty, W3D_CHUNK_SHADER_MATERIAL
from io_mesh_w3d.io_binary import read_chunk_head


class TestShaderMaterial(unittest.TestCase):
    def test_write_read(self):
        expected = ShaderMaterial()
        expected.header = ShaderMaterialHeader(
            number=55,
            type_name="headerType",
            reserver=99)

        self.assertEqual(37, expected.header.size_in_bytes())

        prop1 = ShaderMaterialProperty(
            type=1,
            name="prop1",
            num_chars=44,
            value="test")

        expected.properties.append(prop1)

        prop2 = ShaderMaterialProperty(
            type=2,
            name="prop2",
            num_chars=44,
            value=3.14)

        expected.properties.append(prop2)

        prop3 = ShaderMaterialProperty(
            type=4,
            name="prop3",
            num_chars=44,
            value=Vector((1.0, 2.0, 3.0)))

        expected.properties.append(prop3)

        prop4 = ShaderMaterialProperty(
            type=5,
            name="prop4",
            num_chars=44,
            value=RGBA(r=3, g=1, b=22, a=133))

        expected.properties.append(prop4)

        prop5 = ShaderMaterialProperty(
            type=6,
            name="prop5",
            num_chars=44,
            value=1234)

        expected.properties.append(prop5)

        prop6 = ShaderMaterialProperty(
            type=7,
            name="prop6",
            num_chars=44,
            value=255)

        expected.properties.append(prop6)

        self.assertEqual(223, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_SHADER_MATERIAL, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = ShaderMaterial.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.header.number, actual.header.number)
        self.assertEqual(expected.header.type_name, actual.header.type_name)
        self.assertEqual(expected.header.reserved, actual.header.reserved)

        self.assertEqual(len(expected.properties), len(actual.properties))

        for i, prop in enumerate(expected.properties):
            self.assertEqual(prop.type, actual.properties[i].type)
            self.assertEqual(prop.name, actual.properties[i].name)
            self.assertEqual(prop.num_chars, actual.properties[i].num_chars)
            self.assertAlmostEqual(prop.value, actual.properties[i].value, 5)
