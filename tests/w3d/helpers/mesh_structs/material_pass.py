# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.mesh_structs.material_pass import *
from tests.mathutils import *
from tests.common.helpers.rgba import get_rgba, compare_rgbas


def get_uvs():
    return [get_vec2(0.0, 0.1),
            get_vec2(0.0, 0.4),
            get_vec2(1.0, 0.6),
            get_vec2(0.3, 0.1),
            get_vec2(0.2, 0.2),
            get_vec2(0.6, 0.6),
            get_vec2(0.1, 0.8),
            get_vec2(0.7, 0.7)]


def get_per_face_txcoords():
    return [get_vec(1.0, 0.0, -1.0),
            get_vec(1.0, 0.0, -1.0),
            get_vec(1.0, 0.0, -1.0),
            get_vec(1.0, 0.0, -1.0),
            get_vec(1.0, 0.0, -1.0),
            get_vec(1.0, 0.0, -1.0),
            get_vec(1.0, 0.0, -1.0),
            get_vec(1.0, 0.0, -1.0)]


def get_texture_stage(index=0):
    return TextureStage(
        tx_ids=[[index]],
        per_face_tx_coords=[get_per_face_txcoords()],
        tx_coords=[get_uvs()])


def get_texture_stage_minimal():
    return TextureStage(
        tx_ids=[[0]],
        per_face_tx_coords=[[get_vec()]],
        tx_coords=[[get_vec()]])


def get_texture_stage_empty():
    return TextureStage()


def compare_texture_stages(self, expected, actual):
    if actual.tx_ids:  # roundtrip not yet supported
        self.assertEqual(len(expected.tx_ids), len(actual.tx_ids))
        for i in range(len(expected.tx_ids)):
            for j, tex_id in enumerate(expected.tx_ids[i]):
                self.assertEqual(tex_id, actual.tx_ids[i][j])

    self.assertEqual(len(expected.tx_coords), len(actual.tx_coords))
    for i in range(len(expected.tx_coords)):
        for j, tx_coord in enumerate(expected.tx_coords[i]):
            compare_vectors2(self, tx_coord, actual.tx_coords[i][j])

    if actual.per_face_tx_coords:  # roundtrip not yet supported
        self.assertEqual(len(expected.per_face_tx_coords), len(actual.per_face_tx_coords))
        for i in range(len(expected.per_face_tx_coords)):
            for j, tx_coord in enumerate(expected.per_face_tx_coords[i]):
                compare_vectors(self, tx_coord, actual.per_face_tx_coords[i][j])


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
        matpass.shader_ids = [index]
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
        tx_coords=[get_vec()])


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

    delta = 1
    # because the color floats are truncated to 6 decimal places we
    # have rounding errors on a roundtrip
    if actual.dcg:
        self.assertEqual(len(expected.dcg), len(actual.dcg))
        for i in range(len(expected.dcg)):
            compare_rgbas(self, expected.dcg[i], actual.dcg[i], delta)

    if actual.dig:
        self.assertEqual(len(expected.dig), len(actual.dig))
        for i in range(len(expected.dig)):
            compare_rgbas(self, expected.dig[i], actual.dig[i], delta)

    if actual.scg:
        self.assertEqual(len(expected.scg), len(actual.scg))
        for i in range(len(expected.scg)):
            compare_rgbas(self, expected.scg[i], actual.scg[i], delta)

    self.assertEqual(expected.shader_material_ids, actual.shader_material_ids)

    self.assertEqual(len(expected.tx_coords), len(actual.tx_coords))
    for i in range(len(expected.tx_coords)):
        compare_vectors2(self, expected.tx_coords[i], actual.tx_coords[i])

    self.assertEqual(len(expected.tx_stages), len(actual.tx_stages))
    for i in range(len(expected.tx_stages)):
        compare_texture_stages(
            self, expected.tx_stages[i], actual.tx_stages[i])
