# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest

from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_vertex_material import *

from tests.helpers.w3d_rgba import get_rgba, compare_rgbas


def get_vertex_material_info():
    return VertexMaterialInfo(
        attributes=13,
        ambient=get_rgba(), # alpha is only padding in this and below
        diffuse=get_rgba(),
        specular=get_rgba(),
        emissive=get_rgba(),
        shininess=0.5,
        opacity=0.32,
        translucency=0.12)


def compare_vertex_material_infos(self, expected, actual):
    self.assertEqual(expected.attributes, actual.attributes)
    compare_rgbas(self, expected.ambient, actual.ambient)
    compare_rgbas(self, expected.diffuse, actual.diffuse)
    compare_rgbas(self, expected.specular, actual.specular)
    compare_rgbas(self, expected.emissive, actual.emissive)
    self.assertAlmostEqual(expected.shininess, actual.shininess, 5)
    self.assertAlmostEqual(expected.opacity, actual.opacity, 5)
    self.assertAlmostEqual(expected.translucency, actual.translucency, 5)


def get_vertex_material():
    return VertexMaterial(
        vm_name="VM_NAME",
        vm_info=get_vertex_material_info(),
        vm_args_0="VM_ARGS0",
        vm_args_1="VM_ARGS1")


def compare_vertex_materials(self, expected, actual):
    self.assertEqual(expected.vm_name, actual.vm_name)
    self.assertEqual(expected.vm_args_0, actual.vm_args_0)
    self.assertEqual(expected.vm_args_1, actual.vm_args_1)
    compare_vertex_material_infos(self, expected.vm_info, actual.vm_info)