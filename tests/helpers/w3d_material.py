# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest

from mathutils import Vector

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_material import VertexMaterial, VertexMaterialInfo, \
    MaterialInfo, MaterialPass, TextureStage


def get_vertex_material_info():
    return VertexMaterialInfo(
        attributes=33,
        ambient=RGBA(r=3, g=1, b=44, a=3),
        diffuse=RGBA(r=12, g=4, b=33, a=46),
        specular=RGBA(r=99, g=244, b=255, a=255),
        emissive=RGBA(r=123, g=221, b=33, a=56),
        shininess=67.0,
        opacity=123.0,
        translucency=1335.0)


def compare_vertex_material_infos(self, expected, actual):
    self.assertEqual(expected.attributes, actual.attributes)
    self.assertEqual(expected.ambient, actual.ambient)
    self.assertEqual(expected.diffuse, actual.diffuse)
    self.assertEqual(expected.specular, actual.specular)
    self.assertEqual(expected.emissive, actual.emissive)
    self.assertEqual(expected.shininess, actual.shininess)
    self.assertEqual(expected.opacity, actual.opacity)
    self.assertEqual(expected.translucency, actual.translucency)


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


def get_material_info():
    return MaterialInfo(
        pass_count=33,
        vert_matl_count=123,
        shader_count=43,
        texture_count=142)


def compare_material_infos(self, expected, actual):
    self.assertEqual(expected.pass_count, actual.pass_count)
    self.assertEqual(expected.vert_matl_count, actual.vert_matl_count)
    self.assertEqual(expected.shader_count, actual.shader_count)
    self.assertEqual(expected.texture_count, actual.texture_count)


def get_texture_stage(count = 123):
    tx_stage = TextureStage(
        tx_ids=[],
        per_face_tx_coords=[],
        tx_coords=[])

    for i in range(count):
        tx_stage.tx_ids.append(i)
        tx_stage.tx_coords.append((2, 4))
        tx_stage.per_face_tx_coords.append(Vector((33.0, -2.0, 1.0)))
    return tx_stage


def compare_texture_stages(self, expected, actual):
    self.assertEqual(len(expected.tx_ids), len(actual.tx_ids))
    for i in range(len(expected.tx_ids)):
        self.assertEqual(expected.tx_ids[i], actual.tx_ids[i])
    self.assertEqual(len(expected.tx_coords), len(actual.tx_coords))
    for i in range(len(expected.tx_coords)):
        self.assertAlmostEqual(expected.tx_coords[i], actual.tx_coords[i], 5)
    self.assertEqual(len(expected.per_face_tx_coords), len(actual.per_face_tx_coords))
    for i in range(len(expected.per_face_tx_coords)):
        self.assertAlmostEqual(expected.per_face_tx_coords[i], actual.per_face_tx_coords[i], 5)


def get_material_pass(count=33, num_stages=3):
    matpass = MaterialPass(
        vertex_material_ids=[],
        shader_ids=[],
        dcg=[],
        dig=[],
        scg=[],
        shader_material_ids=[],
        tx_stages=[],
        tx_coords=[])

    for i in range(count):
        matpass.vertex_material_ids.append(i)
        matpass.shader_ids.append(i)
        matpass.dcg.append(RGBA(r=3, g=44, b=133, a=222))
        matpass.dig.append(RGBA(r=3, g=44, b=133, a=222))
        matpass.scg.append(RGBA(r=3, g=44, b=133, a=222))
        matpass.shader_material_ids.append(i)
        matpass.tx_coords.append((0.5, 0.7))

    for _ in range(num_stages):
        matpass.tx_stages.append(get_texture_stage())

    return matpass


def compare_material_passes(self, expected, actual):
    self.assertEqual(expected.vertex_material_ids, actual.vertex_material_ids)
    self.assertEqual(expected.shader_ids, actual.shader_ids)
    self.assertEqual(expected.dcg, actual.dcg)
    self.assertEqual(expected.dig, actual.dig)
    self.assertEqual(expected.scg, actual.scg)
    self.assertEqual(expected.shader_material_ids, actual.shader_material_ids)

    self.assertEqual(len(expected.tx_coords), len(actual.tx_coords))
    for i in range(len(expected.tx_coords)):
        self.assertAlmostEqual(expected.tx_coords[i][0], actual.tx_coords[i][0], 5)
        self.assertAlmostEqual(expected.tx_coords[i][1], actual.tx_coords[i][1], 5)

    self.assertEqual(len(expected.tx_stages), len(actual.tx_stages))
    for i in range(len(expected.tx_stages)):
        compare_texture_stages(self, expected.tx_stages[i], actual.tx_stages[i])
