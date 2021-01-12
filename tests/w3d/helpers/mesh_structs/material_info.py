# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.mesh_structs.material_info import *


def get_material_info(mesh=None):
    info = MaterialInfo(
        pass_count=0,
        vert_matl_count=0,
        shader_count=0,
        texture_count=0)

    if mesh is not None:
        info.pass_count = len(mesh.material_passes)
        info.vert_matl_count = len(mesh.vert_materials)
        info.shader_count = len(mesh.shaders)
        info.texture_count = len(mesh.textures)
    return info


def compare_material_infos(self, expected, actual):
    self.assertEqual(expected.pass_count, actual.pass_count)
    self.assertEqual(expected.vert_matl_count, actual.vert_matl_count)
    self.assertEqual(expected.shader_count, actual.shader_count)
    self.assertEqual(expected.texture_count, actual.texture_count)
