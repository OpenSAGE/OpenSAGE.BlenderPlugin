# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019

from mathutils import Vector
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_shader_material import ShaderMaterial, ShaderMaterialHeader, \
    ShaderMaterialProperty


def get_shader_material_header():
    return ShaderMaterialHeader(
        number=55,
        type_name="headerType",
        reserved=99)

def get_shader_material_property(_type=1):
    result = ShaderMaterialProperty(
        type=_type,
        name="property" + str(_type),
        num_chars=31)

    if _type == 1:
        result.value = "string"
    elif _type == 2:
        result.value = 3.14
    elif _type == 4:
        result.value = Vector((1.0, 2.0, 3.0))
    elif _type == 5:
        result.value = RGBA(r=3, g=1, b=22, a=133)
    elif _type == 6:
        result.value = 1234
    elif _type == 7:
        result.value = 0xff
    return result

def get_shader_material_properties():
    return [
        get_shader_material_property(1),
        get_shader_material_property(2),
        get_shader_material_property(4),
        get_shader_material_property(5),
        get_shader_material_property(6),
        get_shader_material_property(7)
    ]

def get_shader_material(props=get_shader_material_properties()):
    return ShaderMaterial(
        header=get_shader_material_header(),
        properties=props)

def compare_shader_material_headers(self, expected, actual):
    self.assertEqual(expected.number, actual.number)
    self.assertEqual(expected.type_name, actual.type_name)
    self.assertEqual(expected.reserved, actual.reserved)

def compare_shader_material_properties(self, expected, actual):
    self.assertEqual(expected.type, actual.type)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.num_chars, actual.num_chars)
    self.assertAlmostEqual(expected.value, actual.value, 5)

def compare_shader_materials(self, expected, actual):
    compare_shader_material_headers(self, expected.header, actual.header)
    self.assertEqual(len(expected.properties), len(actual.properties))
    for i in range(len(expected.properties)):
        compare_shader_material_properties(self, expected.properties[i], actual.properties[i])

