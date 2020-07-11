# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.mesh_structs.prelit import *
from tests.common.helpers.mesh_structs.texture import *
from tests.w3d.helpers.mesh_structs.material_info import *
from tests.w3d.helpers.mesh_structs.material_pass import *
from tests.w3d.helpers.mesh_structs.shader import *
from tests.w3d.helpers.mesh_structs.vertex_material import *


def get_prelit(prelit_type=W3D_CHUNK_PRELIT_UNLIT, count=1):
    result = PrelitBase(
        prelit_type=prelit_type,
        mat_info=None,
        material_passes=[],
        vert_materials=[],
        textures=[],
        shaders=[])

    result.mat_info = MaterialInfo(
        pass_count=count,
        vert_matl_count=count,
        shader_count=count,
        texture_count=count)

    vm_name = 'INVALID_TYPE'
    if type == W3D_CHUNK_PRELIT_UNLIT:
        vm_name = 'W3D_CHUNK_PRELIT_UNLIT'
    elif type == W3D_CHUNK_PRELIT_VERTEX:
        vm_name = 'W3D_CHUNK_PRELIT_VERTEX'
    elif type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS:
        vm_name = 'W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS'
    elif type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE:
        vm_name = 'W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE'

    for i in range(count):
        result.material_passes.append(get_material_pass())
        name = vm_name + str(i)
        result.vert_materials.append(get_vertex_material(vm_name=name))
        result.textures.append(get_texture())
        result.shaders.append(get_shader())
    return result


def get_prelit_minimal(prelit_type=W3D_CHUNK_PRELIT_UNLIT):
    return PrelitBase(
        prelit_type=prelit_type,
        mat_info=get_material_info(),
        material_passes=[],
        vert_materials=[],
        textures=[],
        shaders=[])


def compare_prelits(self, expected, actual):
    self.assertEqual(expected.prelit_type, actual.prelit_type)
    compare_material_infos(self, expected.mat_info, actual.mat_info)

    self.assertEqual(len(expected.material_passes), len(actual.material_passes))
    for i, mat_pass in enumerate(expected.material_passes):
        compare_material_passes(self, mat_pass, actual.material_passes[i])

    self.assertEqual(len(expected.vert_materials), len(actual.vert_materials))
    for i, vert_mat in enumerate(expected.vert_materials):
        compare_vertex_materials(self, vert_mat, actual.vert_materials[i])

    self.assertEqual(len(expected.textures), len(actual.textures))
    for i, tex in enumerate(expected.textures):
        compare_textures(self, tex, actual.textures[i])

    self.assertEqual(len(expected.shaders), len(actual.shaders))
    for i, shader in enumerate(expected.shaders):
        compare_shaders(self, shader, actual.shaders[i])
