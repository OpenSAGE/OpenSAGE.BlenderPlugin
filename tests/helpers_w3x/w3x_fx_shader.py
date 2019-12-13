# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest

from io_mesh_w3d.structs_w3x.w3x_fx_shader import *
from tests.utils import almost_equal


def compare_constants(self, expected, actual):
    self.assertEqual(expected.type, actual.type)
    self.assertEqual(expected.name, actual.name)

    self.assertEqual(len(expected.values), len(actual.values))
    for i, value in enumerate(expected.values):
        self.assertAlmostEqual(value, actual.values[i], 2)


def get_fx_shader():
    fx_shader = FXShader(
        shader_name="DefaultW3D.fx",
        technique_index=3,
        constants=[])

    fx_shader.constants = [
        Constant(type='Float', name="Opacity", values=["0.314"]),
        Constant(type='Float', name="ColorAmbient", values=["0.314", "0.0", "1.0", "3.0"]),
        Constant(type='Int', name="BlendMode", values=["0"]),
        Constant(type='Bool', name="ColorAmbient", values=["false"]),
        Constant(type='Texture', name="ColorAmbient", values=["texture"])]

    return fx_shader


def get_fx_shader_minimal():
    return FXShader(
        shader_name="DefaultW3D.fx",
        technique_index=3,
        constants=[Constant(type='Float', name="Opacity", values=["0.314"])])


def compare_fx_shaders(self, expected, actual):
    self.assertEqual(expected.shader_name, actual.shader_name)
    self.assertEqual(expected.technique_index, actual.technique_index)

    self.assertEqual(len(expected.constants), len(actual.constants))
    for i in range(len(expected.constants)):
        compare_constants(self, expected.constants[i], actual.constants[i])
