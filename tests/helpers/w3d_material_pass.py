# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest

from mathutils import Vector

from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_material_pass import *

from tests.helpers.w3d_rgba import get_rgba, compare_rgbas


def get_uvs():
    uvs = []
    uvs.append(Vector((0.0, 0.1)))
    uvs.append(Vector((0.0, 0.4)))
    uvs.append(Vector((1.0, 0.6)))
    uvs.append(Vector((0.3, 0.1)))
    uvs.append(Vector((0.2, 0.2)))
    uvs.append(Vector((0.6, 0.6)))
    uvs.append(Vector((0.1, 0.8)))
    uvs.append(Vector((0.7, 0.7)))
    return uvs


def get_per_face_txcoords():
    tx_coords = []
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    tx_coords.append(Vector((1.0, 0.0, -1.0)))
    return tx_coords


def get_texture_stage(index=0):
    return TextureStage(
        tx_ids=[index],
        per_face_tx_coords=get_per_face_txcoords(),
        tx_coords=get_uvs())


def get_texture_stage_minimal():
    return TextureStage(
        tx_ids=[0],
        per_face_tx_coords=[Vector()],
        tx_coords=[Vector()])


def get_texture_stage_empty():
    return TextureStage(
        tx_ids=[],
        per_face_tx_coords=[],
        tx_coords=[])


def compare_texture_stages(self, expected, actual):
    if actual.tx_ids:  # roundtrip not yet supported
        self.assertEqual(len(expected.tx_ids), len(actual.tx_ids))
        for i in range(len(expected.tx_ids)):
            self.assertEqual(expected.tx_ids[i], actual.tx_ids[i])

    self.assertEqual(len(expected.tx_coords), len(actual.tx_coords))
    for i in range(len(expected.tx_coords)):
        self.assertAlmostEqual(
            expected.tx_coords[i][0], actual.tx_coords[i][0], 5)
        self.assertAlmostEqual(
            expected.tx_coords[i][1], actual.tx_coords[i][1], 5)

    if actual.per_face_tx_coords:  # roundtrip not yet supported
        self.assertEqual(len(expected.per_face_tx_coords),
                         len(actual.per_face_tx_coords))
        for i in range(len(expected.per_face_tx_coords)):
            self.assertAlmostEqual(
                expected.per_face_tx_coords[i][0],
                actual.per_face_tx_coords[i][0],
                5)
            self.assertAlmostEqual(
                expected.per_face_tx_coords[i][1],
                actual.per_face_tx_coords[i][1],
                5)
            self.assertAlmostEqual(
                expected.per_face_tx_coords[i][2],
                actual.per_face_tx_coords[i][2],
                5)


def get_material_pass(index=0, shader_mat=False, num_stages=1):
    matpass = MaterialPass(
        vertex_material_ids=[],
        shader_ids=[],
        dcg=[],
        dig=[],
        scg=[],
        shader_material_ids=[],
        tx_stages=[],
        tx_coords=[])

    if shader_mat:
        matpass.shader_material_ids = [index]
        matpass.tx_coords = get_uvs()
    else:
        matpass.shader_ids=[index]
        matpass.vertex_material_ids = [index]
        for i in range(num_stages):
            matpass.tx_stages.append(get_texture_stage(index=index + i))

    for _ in range(8):
        matpass.dcg.append(get_rgba())
        matpass.dig.append(get_rgba())
        matpass.scg.append(get_rgba())

    return matpass


def get_material_pass_minimal():
    return MaterialPass(
        vertex_material_ids=[0],
        shader_ids=[0],
        dcg=[get_rgba()],
        dig=[get_rgba()],
        scg=[get_rgba()],
        shader_material_ids=[0],
        tx_stages=[get_texture_stage()],
        tx_coords=[Vector()])


def get_material_pass_empty():
    return MaterialPass(
        vertex_material_ids=[],
        shader_ids=[],
        dcg=[],
        dig=[],
        scg=[],
        shader_material_ids=[],
        tx_stages=[],
        tx_coords=[])


def compare_material_passes(self, expected, actual):
    self.assertEqual(expected.vertex_material_ids, actual.vertex_material_ids)
    self.assertEqual(expected.shader_ids, actual.shader_ids)

    if actual.dcg:  # roundtrip not supported yet
        self.assertEqual(len(expected.dcg), len(actual.dcg))
        for i in range(len(expected.dcg)):
            compare_rgbas(self, expected.dcg[i], actual.dcg[i])

    if actual.dig:  # roundtrip not supported yet
        self.assertEqual(len(expected.dig), len(actual.dig))
        for i in range(len(expected.dig)):
            compare_rgbas(self, expected.dig[i], actual.dig[i])

    if actual.scg:  # roundtrip not supported yet
        self.assertEqual(len(expected.scg), len(actual.scg))
        for i in range(len(expected.scg)):
            compare_rgbas(self, expected.scg[i], actual.scg[i])

    self.assertEqual(expected.shader_material_ids, actual.shader_material_ids)

    self.assertEqual(len(expected.tx_coords), len(actual.tx_coords))
    for i in range(len(expected.tx_coords)):
        self.assertAlmostEqual(
            expected.tx_coords[i][0], actual.tx_coords[i][0], 5)
        self.assertAlmostEqual(
            expected.tx_coords[i][1], actual.tx_coords[i][1], 5)

    self.assertEqual(len(expected.tx_stages), len(actual.tx_stages))
    for i in range(len(expected.tx_stages)):
        compare_texture_stages(
            self, expected.tx_stages[i], actual.tx_stages[i])
