# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.mesh_structs.shader_material import *
from tests.mathutils import *


def get_shader_material_header(name):
    return ShaderMaterialHeader(
        version=1,
        type_name=name,
        technique=0)


def compare_shader_material_headers(self, expected, actual):
    self.assertEqual(expected.version, actual.version)
    self.assertEqual(expected.type_name, actual.type_name)
    self.assertEqual(expected.technique, actual.technique)


def get_shader_material_property(
        prop_type=1, name='property', tex_name='texture.dds', value=None):
    result = ShaderMaterialProperty(
        prop_type=prop_type,
        name=name)

    if value is not None:
        result.value = value
    elif prop_type == STRING_PROPERTY:
        result.value = tex_name
    elif prop_type == FLOAT_PROPERTY:
        result.value = 0.25
    elif prop_type == VEC2_PROPERTY:
        result.value = get_vec2(x=1.0, y=0.5)
    elif prop_type == VEC3_PROPERTY:
        result.value = get_vec(x=1.0, y=0.2, z=0.33)
    elif prop_type == VEC4_PROPERTY:
        result.value = get_vec4(x=0.33, y=0.3, z=0.1, w=1.0)
    elif prop_type == LONG_PROPERTY:
        result.value = 3
    elif prop_type == BOOL_PROPERTY:
        result.value = True
    return result


def compare_shader_material_properties(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.prop_type, actual.prop_type, 'Incorrect type: ' +
                     str(actual.prop_type) + ' for property: ' + actual.name)

    if expected.prop_type == STRING_PROPERTY:
        self.assertEqual(expected.value.split('.')[0], actual.value.split('.')[0])
    elif expected.prop_type == FLOAT_PROPERTY:
        self.assertAlmostEqual(expected.value, actual.value, 5)
    elif expected.prop_type == VEC2_PROPERTY:
        compare_vectors2(self, expected.value, actual.value)
    elif expected.prop_type == VEC3_PROPERTY:
        compare_vectors(self, expected.value, actual.value)
    elif expected.prop_type == VEC4_PROPERTY:
        compare_vectors4(self, expected.value, actual.value)
    else:
        self.assertEqual(expected.value, actual.value)


def get_shader_material_properties(name, rgb_color=False):
    if name == 'NormalMapped.fx':
        ambient = get_shader_material_property(VEC4_PROPERTY, 'AmbientColor')
        if rgb_color:
            ambient = get_shader_material_property(VEC3_PROPERTY, 'AmbientColor')

        return [
            get_shader_material_property(VEC4_PROPERTY, 'DiffuseColor'),
            get_shader_material_property(STRING_PROPERTY, 'DiffuseTexture'),
            get_shader_material_property(BOOL_PROPERTY, 'AlphaTestEnable', value=False),
            get_shader_material_property(STRING_PROPERTY, 'NormalMap', 'texture_nrm.dds'),
            get_shader_material_property(FLOAT_PROPERTY, 'BumpScale'),
            ambient,
            get_shader_material_property(VEC4_PROPERTY, 'SpecularColor'),
            get_shader_material_property(FLOAT_PROPERTY, 'SpecularExponent')]

    elif name == 'BasicW3D.fx':
        return [
            get_shader_material_property(VEC4_PROPERTY, 'ColorDiffuse'),
            get_shader_material_property(STRING_PROPERTY, 'Texture_0'),
            get_shader_material_property(STRING_PROPERTY, 'Texture_1', 'texture_1.dds'),
            get_shader_material_property(BOOL_PROPERTY, 'AlphaTestEnable', value=False),
            get_shader_material_property(VEC4_PROPERTY, 'ColorAmbient'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorSpecular'),
            get_shader_material_property(FLOAT_PROPERTY, 'Shininess'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorEmissive'),
            get_shader_material_property(BOOL_PROPERTY, 'DepthWriteEnable'),
            get_shader_material_property(BOOL_PROPERTY, 'CullingEnable'),
            get_shader_material_property(LONG_PROPERTY, 'BlendMode')]

    elif name == 'DefaultW3D.fx':
        return [
            get_shader_material_property(VEC4_PROPERTY, 'ColorDiffuse'),
            get_shader_material_property(STRING_PROPERTY, 'Texture_0'),
            get_shader_material_property(STRING_PROPERTY, 'Texture_1', 'texture_1.dds'),
            get_shader_material_property(BOOL_PROPERTY, 'AlphaTestEnable', value=False),
            get_shader_material_property(VEC4_PROPERTY, 'ColorAmbient'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorSpecular'),
            get_shader_material_property(FLOAT_PROPERTY, 'Shininess'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorEmissive'),
            get_shader_material_property(FLOAT_PROPERTY, 'Opacity'),
            get_shader_material_property(LONG_PROPERTY, 'NumTextures'),
            get_shader_material_property(BOOL_PROPERTY, 'DepthWriteEnable'),
            get_shader_material_property(BOOL_PROPERTY, 'CullingEnable'),
            get_shader_material_property(LONG_PROPERTY, 'BlendMode'),
            get_shader_material_property(FLOAT_PROPERTY, 'EdgeFadeOut'),
            get_shader_material_property(BOOL_PROPERTY, 'UseRecolorColors'),
            get_shader_material_property(BOOL_PROPERTY, 'HouseColorPulse'),
            get_shader_material_property(LONG_PROPERTY, 'SecondaryTextureBlendMode'),
            get_shader_material_property(VEC4_PROPERTY, 'TexCoordMapper_0'),
            get_shader_material_property(VEC4_PROPERTY, 'TexCoordTransform_0'),
            get_shader_material_property(VEC4_PROPERTY, 'TextureAnimation_FPS_NumPerRow_LastFrame_FrameOffset_0'),
            get_shader_material_property(LONG_PROPERTY, 'TexCoordMapper_1'),
            get_shader_material_property(VEC4_PROPERTY, 'TexCoordTransform_1'),
            get_shader_material_property(VEC4_PROPERTY, 'Sampler_ClampU_ClampV_NoMip_0'),
            get_shader_material_property(VEC4_PROPERTY, 'Sampler_ClampU_ClampV_NoMip_1')]

    elif name == 'Infantry.fx':
        return [
            get_shader_material_property(VEC4_PROPERTY, 'ColorDiffuse'),
            get_shader_material_property(STRING_PROPERTY, 'Texture_0'),
            get_shader_material_property(STRING_PROPERTY, 'Texture_1', 'texture_1.dds'),
            get_shader_material_property(BOOL_PROPERTY, 'AlphaTestEnable', value=False),
            get_shader_material_property(STRING_PROPERTY, 'RecolorTexture', 'texture_rec.dds'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorAmbient'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorSpecular'),
            get_shader_material_property(FLOAT_PROPERTY, 'Shininess'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorEmissive'),
            get_shader_material_property(BOOL_PROPERTY, 'DepthWriteEnable'),
            get_shader_material_property(BOOL_PROPERTY, 'CullingEnable'),
            get_shader_material_property(LONG_PROPERTY, 'BlendMode')]

    elif name == 'MuzzleFlash.fx':
        return [
            get_shader_material_property(STRING_PROPERTY, 'Texture_0'),
            get_shader_material_property(VEC4_PROPERTY, 'ColorEmissive'),
            get_shader_material_property(FLOAT_PROPERTY, 'TexCoordTransformAngle_0'),
            get_shader_material_property(FLOAT_PROPERTY, 'TexCoordTransformU_0'),
            get_shader_material_property(FLOAT_PROPERTY, 'TexCoordTransformV_0'),
            get_shader_material_property(FLOAT_PROPERTY, 'TexCoordTransformU_1'),
            get_shader_material_property(FLOAT_PROPERTY, 'TexCoordTransformV_1'),
            get_shader_material_property(FLOAT_PROPERTY, 'TexCoordTransformU_2'),
            get_shader_material_property(FLOAT_PROPERTY, 'TexCoordTransformV_2')]

    elif name == 'ObjectsGDI.fx':
        return [
            get_shader_material_property(VEC4_PROPERTY, 'DiffuseColor'),
            get_shader_material_property(STRING_PROPERTY, 'DiffuseTexture'),
            get_shader_material_property(BOOL_PROPERTY, 'AlphaTestEnable', value=False),
            get_shader_material_property(STRING_PROPERTY, 'NormalMap', 'texture_nrm.dds'),
            get_shader_material_property(FLOAT_PROPERTY, 'BumpScale'),
            get_shader_material_property(VEC4_PROPERTY, 'AmbientColor'),
            get_shader_material_property(VEC4_PROPERTY, 'SpecularColor'),
            get_shader_material_property(FLOAT_PROPERTY, 'SpecularExponent'),
            get_shader_material_property(STRING_PROPERTY, 'SpecMap', 'texture_spec.dds'),
            get_shader_material_property(STRING_PROPERTY, 'RecolorTexture', 'texture_rec.dds'),
            get_shader_material_property(FLOAT_PROPERTY, 'EnvMult')]

    elif name == 'ObjectsAlien.fx':
        return [
            get_shader_material_property(VEC4_PROPERTY, 'DiffuseColor'),
            get_shader_material_property(STRING_PROPERTY, 'DiffuseTexture'),
            get_shader_material_property(BOOL_PROPERTY, 'AlphaTestEnable', value=False),
            get_shader_material_property(STRING_PROPERTY, 'NormalMap', 'texture_nrm.dds'),
            get_shader_material_property(FLOAT_PROPERTY, 'BumpScale'),
            get_shader_material_property(VEC4_PROPERTY, 'AmbientColor'),
            get_shader_material_property(VEC4_PROPERTY, 'SpecularColor'),
            get_shader_material_property(FLOAT_PROPERTY, 'SpecularExponent'),
            get_shader_material_property(STRING_PROPERTY, 'SpecMap', 'texture_spec.dds'),
            get_shader_material_property(STRING_PROPERTY, 'RecolorTexture', 'texture_rec.dds'),
            get_shader_material_property(FLOAT_PROPERTY, 'EnvMult'),
            get_shader_material_property(STRING_PROPERTY, 'EnvironmentTexture', 'texture_env.dds')]

    elif name == 'ObjectsNOD.fx':
        return [
            get_shader_material_property(VEC4_PROPERTY, 'DiffuseColor'),
            get_shader_material_property(STRING_PROPERTY, 'DiffuseTexture'),
            get_shader_material_property(BOOL_PROPERTY, 'AlphaTestEnable', value=False),
            get_shader_material_property(STRING_PROPERTY, 'NormalMap', 'texture_nrm.dds'),
            get_shader_material_property(FLOAT_PROPERTY, 'BumpScale'),
            get_shader_material_property(VEC4_PROPERTY, 'AmbientColor'),
            get_shader_material_property(VEC4_PROPERTY, 'SpecularColor'),
            get_shader_material_property(FLOAT_PROPERTY, 'SpecularExponent'),
            get_shader_material_property(STRING_PROPERTY, 'SpecMap', 'texture_spec.dds'),
            get_shader_material_property(STRING_PROPERTY, 'ScrollingMaskTexture', 'texture_scroll.dds'),
            get_shader_material_property(VEC4_PROPERTY, 'TexCoordTransform_0'),
            get_shader_material_property(FLOAT_PROPERTY, 'RecolorMultiplier'),
            get_shader_material_property(FLOAT_PROPERTY, 'EnvMult')]

    print('NO SHADER PROPERTY SET DEFINED FOR : ' + name)
    return []


def get_shader_material(name='NormalMapped.fx', rgb_colors=False):
    return ShaderMaterial(
        header=get_shader_material_header(name),
        properties=get_shader_material_properties(name, rgb_colors))


def get_shader_material_minimal():
    shader_mat = ShaderMaterial(
        header=get_shader_material_header('Minimal.fx'))

    shader_mat.properties = [
        get_shader_material_property(STRING_PROPERTY, 'a'),
        get_shader_material_property(FLOAT_PROPERTY, 'b'),
        get_shader_material_property(VEC2_PROPERTY, 'c'),
        get_shader_material_property(VEC3_PROPERTY, 'd'),
        get_shader_material_property(VEC4_PROPERTY, 'e'),
        get_shader_material_property(LONG_PROPERTY, 'f'),
        get_shader_material_property(BOOL_PROPERTY, 'g')]
    return shader_mat


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

        self.assertTrue(match_found, 'Unexpected property ' + actual_prop.name +
                        ' in result! value: ' + str(actual_prop.value))

    self.assertEqual(len(expected.properties), len(actual.properties))
