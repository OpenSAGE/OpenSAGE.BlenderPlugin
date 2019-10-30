# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest

from mathutils import Vector

from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_material_pass import *

from tests.helpers.w3d_rgba import get_rgba, compare_rgbas


def get_uvs():
    uvs = []
    uvs.append((0.0, 0.1))
    uvs.append((0.0, 0.4))
    uvs.append((1.0, 0.6))
    uvs.append((0.3, 0.1))
    uvs.append((0.2, 0.2))
    uvs.append((0.6, 0.6))
    uvs.append((0.1, 0.8))
    uvs.append((0.7, 0.7))
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


def get_texture_stage(index=0, minimal=False):
    tx_stage = TextureStage(
        tx_ids=[],
        per_face_tx_coords=[],
        tx_coords=[])

    if minimal:
        return tx_stage

    tx_stage.tx_ids = [index]
    tx_stage.tx_coords = get_uvs()
    tx_stage.per_face_tx_coords = get_per_face_txcoords()
    return tx_stage


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
                expected.per_face_tx_coords[i][0], actual.per_face_tx_coords[i][0], 5)
            self.assertAlmostEqual(
                expected.per_face_tx_coords[i][1], actual.per_face_tx_coords[i][1], 5)
            self.assertAlmostEqual(
                expected.per_face_tx_coords[i][2], actual.per_face_tx_coords[i][2], 5)


def get_material_pass(index=0, minimal=False, shader_mat=False):
    matpass = MaterialPass(
        vertex_material_ids=[],
        shader_ids=[],
        dcg=[],
        dig=[],
        scg=[],
        shader_material_ids=[],
        tx_stages=[],
        tx_coords=[])

    if minimal:
        return matpass

    matpass.shader_ids = [index]

    if shader_mat:
        matpass.shader_material_ids = [index]
    else:
        matpass.vertex_material_ids = [index]

    for _ in range(8):
        matpass.dcg.append(get_rgba())
        matpass.dig.append(get_rgba())
        matpass.scg.append(get_rgba())

    if shader_mat:
        matpass.tx_coords = get_uvs()
    else:
        matpass.tx_stages.append(get_texture_stage(index=index))
        # matpass.tx_stages.append(get_texture_stage()) # only one tx_stage allowed for now

    return matpass


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
