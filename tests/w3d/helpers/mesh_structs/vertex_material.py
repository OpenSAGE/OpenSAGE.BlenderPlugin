# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *

from tests.common.helpers.rgba import get_rgba, compare_rgbas


def get_vertex_material_info(attributes=0):
    return VertexMaterialInfo(
        attributes=attributes,
        ambient=get_rgba(a=0),  # alpha is only padding in this and below
        diffuse=get_rgba(a=0),
        specular=get_rgba(a=0),
        emissive=get_rgba(a=0),
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


def get_vertex_material(vm_name='VM_NAME'):
    attrs = USE_DEPTH_CUE | ARGB_EMISSIVE_ONLY | COPY_SPECULAR_TO_DIFFUSE \
        | DEPTH_CUE_TO_ALPHA
    return VertexMaterial(
        vm_name=vm_name,
        vm_info=get_vertex_material_info(
            attributes=attrs),
        vm_args_0='VM_ARGS0',
        vm_args_1='VM_ARGS1')


def get_vertex_material_minimal():
    return VertexMaterial(
        vm_name='a',
        vm_info=get_vertex_material_info(),
        vm_args_0='a',
        vm_args_1='a')


def get_vertex_material_empty():
    return VertexMaterial(
        vm_name='a',
        vm_info=None,
        vm_args_0='',
        vm_args_1='')


def compare_vertex_materials(self, expected, actual):
    self.assertEqual(expected.vm_name.split('.')[0], actual.vm_name.split('.')[0])
    self.assertEqual(expected.vm_args_0, actual.vm_args_0)
    self.assertEqual(expected.vm_args_1, actual.vm_args_1)
    if expected.vm_info is not None:
        compare_vertex_material_infos(self, expected.vm_info, actual.vm_info)
    else:
        self.assertIsNone(actual.vm_info)
