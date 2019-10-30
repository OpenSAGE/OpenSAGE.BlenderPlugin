# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019

from mathutils import Vector

from io_mesh_w3d.structs.w3d_shader_material import ShaderMaterial, ShaderMaterialHeader, \
    ShaderMaterialProperty

from tests.helpers.w3d_rgba import get_rgba, compare_rgbas


def get_shader_material_header():
    return ShaderMaterialHeader(
        number=55,
        type_name="headerType",
        reserved=0)

def get_shader_material_property(_type=1, name="property"):
    result = ShaderMaterialProperty(
        type=_type,
        name=name,
        num_chars=0)

    if _type == 1:
        result.value = "texture.dds"
    elif _type == 2:
        result.value = 0.25
    elif _type == 3:
        result.value = Vector((1.0, 0.5))
    elif _type == 4:
        result.value = Vector((1.0, 0.2, 0.33))
    elif _type == 5:
        result.value = get_rgba()
    elif _type == 6:
        result.value = 3
    elif _type == 7:
        result.value = True
    return result

def get_shader_material_properties():
    return [
        get_shader_material_property(1, "DiffuseTexture"),
        get_shader_material_property(1, "NormalMap"),
        get_shader_material_property(2, "BumpScale"),
        get_shader_material_property(2, "SpecularExponent"),
        get_shader_material_property(3, "BumpUVScale"),
        get_shader_material_property(4, "Sampler_ClampU_ClampV_NoMip_0"),
        get_shader_material_property(5, "AmbientColor"),
        get_shader_material_property(5, "DiffuseColor"),
        get_shader_material_property(5, "SpecularColor"),
        get_shader_material_property(6, "BlendMode"),
        get_shader_material_property(7, "AlphaTestEnable")
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

    if expected.type == 2:
        self.assertAlmostEqual(expected.value, actual.value, 5)
    elif expected.type == 5:
        compare_rgbas(self, expected.value, actual.value)
    else:
        self.assertEqual(expected.value, actual.value)

def compare_shader_materials(self, expected, actual):
    compare_shader_material_headers(self, expected.header, actual.header)
    self.assertEqual(len(expected.properties), len(actual.properties))
    for i in range(len(expected.properties)):
        compare_shader_material_properties(self, expected.properties[i], actual.properties[i])

