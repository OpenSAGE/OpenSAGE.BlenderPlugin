# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs.w3d_shader_material import *
from tests.helpers.w3d_rgba import get_rgba, compare_rgbas
from tests.helpers.mathutils import *

from io_mesh_w3d.w3d.structs.mesh_structs.shader_material import *

from tests.w3d.helpers.rgba import get_rgba, compare_rgbas


def get_shader_material_header():
    return ShaderMaterialHeader(
        number=1,
        type_name="NormalMapped.fx",
        reserved=2)


def compare_shader_material_headers(self, expected, actual):
    self.assertEqual(expected.number, actual.number)
    self.assertEqual(expected.type_name, actual.type_name)
    self.assertEqual(expected.reserved, actual.reserved)


def get_shader_material_property(_type=1, name="property", tex_name="texture.dds"):
    result = ShaderMaterialProperty(
        type=_type,
        name=name)

    if _type == 1:
        result.value = tex_name
    elif _type == 2:
        result.value = 0.25
    elif _type == 3:
        result.value = get_vector2(x=1.0, y=0.5)
    elif _type == 4:
        result.value = get_vector(x=1.0, y=0.2, z=0.33)
    elif _type == 5:
        result.value = get_rgba()
    elif _type == 6:
        result.value = 3
    elif _type == 7:
        result.value = True
    return result


def compare_shader_material_properties(self, expected, actual):
    self.assertEqual(expected.type, actual.type)
    self.assertEqual(expected.name, actual.name)

    if expected.type == 2:
        self.assertAlmostEqual(expected.value, actual.value, 5)
    elif expected.type == 3:
        compare_vectors2(self, expected.value, actual.value)
    elif expected.type == 4:
        compare_vectors(self, expected.value, actual.value)
    elif expected.type == 5:
        compare_rgbas(self, expected.value, actual.value)

    else:
        self.assertEqual(expected.value, actual.value)


def get_shader_material_properties():
    return [
        get_shader_material_property(1, "DiffuseTexture"),
        get_shader_material_property(1, "NormalMap", "texture_nrm.dds"),
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


def get_shader_material():
    return ShaderMaterial(
        header=get_shader_material_header(),
        properties=get_shader_material_properties())


def get_shader_material_minimal():
    shader_mat = ShaderMaterial(
        header=get_shader_material_header(),
        properties=[])

    shader_mat.properties = [
        get_shader_material_property(1, "a"),
        get_shader_material_property(2, "a"),
        get_shader_material_property(3, "a"),
        get_shader_material_property(4, "a"),
        get_shader_material_property(5, "a"),
        get_shader_material_property(6, "a"),
        get_shader_material_property(7, "a")]
    return shader_mat


def get_shader_material_empty():
    return ShaderMaterial(
        header=get_shader_material_header(),
        properties=[])


def compare_shader_materials(self, expected, actual):
    compare_shader_material_headers(self, expected.header, actual.header)
    self.assertEqual(len(expected.properties), len(actual.properties))
    for i in range(len(expected.properties)):
        compare_shader_material_properties(
            self, expected.properties[i], actual.properties[i])
