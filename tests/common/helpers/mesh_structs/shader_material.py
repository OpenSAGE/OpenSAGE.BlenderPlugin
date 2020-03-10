# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.mesh_structs.shader_material import *
from tests.mathutils import *


def get_shader_material_header():
    return ShaderMaterialHeader(
        version=1,
        type_name='NormalMapped.fx',
        technique=0)


def compare_shader_material_headers(self, expected, actual):
    self.assertEqual(expected.version, actual.version)
    self.assertEqual(expected.type_name, actual.type_name)
    self.assertEqual(expected.technique, actual.technique)


def get_shader_material_property(
        _type=1, name='property', tex_name='texture.dds', value=None):
    result = ShaderMaterialProperty(
        type=_type,
        name=name)

    if value is not None:
        result.value = value
    elif _type == 1:
        result.value = tex_name
    elif _type == 2:
        result.value = 0.25
    elif _type == 3:
        result.value = get_vec2(x=1.0, y=0.5)
    elif _type == 4:
        result.value = get_vec(x=1.0, y=0.2, z=0.33)
    elif _type == 5:
        result.value = get_vec4(x=0.33, y=0.3, z=0.1, w=1.0)
    elif _type == 6:
        result.value = 3
    elif _type == 7:
        result.value = True
    return result


def compare_shader_material_properties(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.type, actual.type, 'Incorrect type: ' +
                     str(actual.type) + ' for property: ' + actual.name)

    if expected.type == 1:
        self.assertEqual(expected.value.split('.')[0], actual.value.split('.')[0])
    elif expected.type == 2:
        self.assertAlmostEqual(expected.value, actual.value, 5)
    elif expected.type == 3:
        compare_vectors2(self, expected.value, actual.value)
    elif expected.type == 4:
        compare_vectors(self, expected.value, actual.value)
    elif expected.type == 5:
        compare_vectors4(self, expected.value, actual.value)
    else:
        self.assertEqual(expected.value, actual.value)


def get_shader_material_properties(w3x=False, two_tex=False, rgb_colors=False):
    props = [
        get_shader_material_property(3, 'BumpUVScale'),
        get_shader_material_property(6, 'BlendMode'),
        get_shader_material_property(7, 'AlphaTestEnable', value=False),
        get_shader_material_property(7, 'CullingEnable'),
        get_shader_material_property(2, 'Opacity'),
        get_shader_material_property(6, 'EdgeFadeOut'),
        get_shader_material_property(7, 'DepthWriteEnable'),
        get_shader_material_property(5, 'Sampler_ClampU_ClampV_NoMip_0'),
        get_shader_material_property(5, 'Sampler_ClampU_ClampV_NoMip_1'),
        get_shader_material_property(1, 'EnvironmentTexture', 'texture_env.tga'),
        get_shader_material_property(2, 'EnvMult'),
        get_shader_material_property(1, 'RecolorTexture'),
        get_shader_material_property(2, 'RecolorMultiplier'),
        get_shader_material_property(7, 'UseRecolorColors'),
        get_shader_material_property(7, 'HouseColorPulse'),
        get_shader_material_property(1, 'ScrollingMaskTexture', 'texture_scroll.dds'),
        get_shader_material_property(2, 'TexCoordTransformAngle_0'),
        get_shader_material_property(2, 'TexCoordTransformU_0'),
        get_shader_material_property(2, 'TexCoordTransformV_0'),
        get_shader_material_property(2, 'TexCoordTransformU_1'),
        get_shader_material_property(2, 'TexCoordTransformV_1'),
        get_shader_material_property(2, 'TexCoordTransformU_2'),
        get_shader_material_property(2, 'TexCoordTransformV_2'),
        get_shader_material_property(5, 'TextureAnimation_FPS_NumPerRow_LastFrame_FrameOffset_0'),
        get_shader_material_property(1, 'IonHullTexture'),
        get_shader_material_property(7, 'MultiTextureEnable')]

    if w3x:
        props.append(get_shader_material_property(2, 'Shininess', value=125.0))

        if rgb_colors:
            props.append(get_shader_material_property(4, 'ColorDiffuse', value=get_vec(x=0.2, y=0.33, z=0.9)))
            props.append(get_shader_material_property(4, 'ColorSpecular', value=get_vec(x=0.2, y=0.33, z=0.9)))
            props.append(get_shader_material_property(4, 'ColorAmbient', value=get_vec(x=0.2, y=0.33, z=0.9)))
            props.append(get_shader_material_property(4, 'ColorEmissive', value=get_vec(x=0.2, y=0.33, z=0.9)))
        else:
            props.append(get_shader_material_property(5, 'ColorDiffuse'))
            props.append(get_shader_material_property(5, 'ColorSpecular'))
            props.append(get_shader_material_property(5, 'ColorAmbient'))
            props.append(get_shader_material_property(5, 'ColorEmissive'))
    else:
        props.append(get_shader_material_property(2, 'SpecularExponent', value=125.0))
        props.append(get_shader_material_property(5, 'DiffuseColor'))
        props.append(get_shader_material_property(5, 'SpecularColor'))
        props.append(get_shader_material_property(5, 'AmbientColor'))
        props.append(get_shader_material_property(5, 'EmissiveColor'))

    if two_tex:
        props.append(get_shader_material_property(6, 'NumTextures', value=2))
        props.append(get_shader_material_property(1, 'Texture_0', 'texture_0.dds'))
        props.append(get_shader_material_property(1, 'Texture_1', 'texture_1.dds'))
        props.append(get_shader_material_property(6, 'SecondaryTextureBlendMode'))
        props.append(get_shader_material_property(6, 'TexCoordMapper_0'))
        props.append(get_shader_material_property(6, 'TexCoordMapper_1'))
        props.append(get_shader_material_property(5, 'TexCoordTransform_0'))
        props.append(get_shader_material_property(5, 'TexCoordTransform_1'))
    else:
        props.append(get_shader_material_property(1, 'DiffuseTexture'))
        props.append(get_shader_material_property(1, 'NormalMap', 'texture_nrm.dds'))
        props.append(get_shader_material_property(2, 'BumpScale'))
        props.append(get_shader_material_property(1, 'SpecMap', 'texture_spec.dds'))
    return props


def get_shader_material_properties_minimal():
    return [
        get_shader_material_property(2, 'SpecularExponent'),
        get_shader_material_property(3, 'BumpUVScale'),
        get_shader_material_property(4, 'SpecularColor'),
        get_shader_material_property(5, 'AmbientColor'),
        get_shader_material_property(5, 'DiffuseColor'),
        get_shader_material_property(6, 'BlendMode'),
        get_shader_material_property(7, 'AlphaTestEnable', value=False)]


def get_shader_material(w3x=False, two_tex=False, rgb_colors=False):
    return ShaderMaterial(
        header=get_shader_material_header(),
        properties=get_shader_material_properties(w3x, two_tex, rgb_colors))


def get_shader_material_minimal():
    shader_mat = ShaderMaterial(
        header=get_shader_material_header(),
        properties=[])

    shader_mat.properties = [
        get_shader_material_property(1, 'a'),
        get_shader_material_property(2, 'b'),
        get_shader_material_property(3, 'c'),
        get_shader_material_property(4, 'd'),
        get_shader_material_property(5, 'e'),
        get_shader_material_property(6, 'f'),
        get_shader_material_property(7, 'g')]
    return shader_mat


def get_shader_material_empty():
    return ShaderMaterial(
        header=get_shader_material_header(),
        properties=[])


def compare_shader_materials(self, expected, actual):
    compare_shader_material_headers(self, expected.header, actual.header)

    for expected_prop in expected.properties:
        match_found = False
        for actual_prop in actual.properties:
            if actual_prop.name == expected_prop.name:
                compare_shader_material_properties(
                    self, expected_prop, actual_prop)
                match_found = True

        self.assertTrue(match_found, 'No matching property ' + expected_prop.name + ' found!')

    for actual_prop in actual.properties:
        match_found = False
        for expected_prop in expected.properties:
            if actual_prop.name == expected_prop.name:
                match_found = True

        self.assertTrue(match_found, 'Unexpected property ' + actual_prop.name + ' in result!' + str(actual_prop.value))

    self.assertEqual(len(expected.properties), len(actual.properties))
