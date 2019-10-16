# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from mathutils import Vector
from io_mesh_w3d.structs.w3d_version import Version

from io_mesh_w3d.structs.w3d_mesh import Mesh, MeshHeader, GEOMETRY_TYPE_SKIN
from tests.helpers.w3d_material import get_material_info, compare_material_infos, \
    get_vertex_material, compare_vertex_materials, get_material_pass, compare_material_passes
from tests.helpers.w3d_shader import get_shader, compare_shaders
from tests.helpers.w3d_texture import get_texture, compare_textures
from tests.helpers.w3d_shader_material import get_shader_material, compare_shader_materials
from tests.helpers.w3d_aabbtree import get_aabbtree, compare_aabbtrees
from tests.helpers.w3d_triangle import get_triangle, compare_triangles
from tests.helpers.w3d_vertex_influence import get_vertex_influence, compare_vertex_influences

def get_mesh_header(name, skin):
    header = MeshHeader(
        version=Version(minor=3, major=1),
        attrs=0,
        mesh_name=name,
        container_name="contName",
        face_count=3,
        vert_count=32,
        matl_count=11,
        damage_stage_count=3,
        sort_level=3,
        prelit_version=2,
        future_count=44,
        vert_channel_flags=3,
        face_channel_flags=3,
        min_corner=Vector((0.0, 0.0, 0.0)),
        max_corner=Vector((0.0, 0.0, 0.0)),
        sph_center=Vector((0.0, 0.0, 0.0)),
        sph_radius=0.0)

    if skin:
        header.attrs = GEOMETRY_TYPE_SKIN
    return header


def compare_mesh_headers(self, expected, actual):
    self.assertEqual(expected.version, actual.version)
    self.assertEqual(expected.attrs, actual.attrs)
    self.assertEqual(expected.mesh_name, actual.mesh_name)
    self.assertEqual(expected.container_name, actual.container_name)
    self.assertEqual(expected.face_count, actual.face_count)
    self.assertEqual(expected.vert_count, actual.vert_count)
    self.assertEqual(expected.matl_count, actual.matl_count)
    self.assertEqual(expected.damage_stage_count, actual.damage_stage_count)
    self.assertEqual(expected.sort_level, actual.sort_level)
    self.assertEqual(expected.prelit_version, actual.prelit_version)
    self.assertEqual(expected.future_count, actual.future_count)
    self.assertEqual(expected.vert_channel_flags, actual.vert_channel_flags)
    self.assertEqual(expected.face_channel_flags, actual.face_channel_flags)
    self.assertEqual(expected.min_corner, actual.min_corner)
    self.assertEqual(expected.max_corner, actual.max_corner)
    self.assertEqual(expected.sph_center, actual.sph_center)
    self.assertEqual(expected.sph_radius, actual.sph_radius)


def get_mesh(name="meshName", skin=False, minimal=False):
    mesh = Mesh(
        header=get_mesh_header(name, skin),
        user_text="",
        verts=[],
        normals=[],
        vert_infs=[],
        triangles=[],
        shade_ids=[],
        mat_info=None,
        shaders=[],
        vert_materials=[],
        textures=[],
        shader_materials=[],
        material_pass=None,
        aabbtree=None)

    if minimal:
        return mesh

    mesh.user_text = "TestUserText"

    for i in range(332):
        mesh.verts.append(Vector((3.0, -1.2, 0.0)))
        mesh.normals.append(Vector((3.0, -1.2, 0.0)))
        mesh.vert_infs.append(get_vertex_influence(bone=1, xtra=2))
        mesh.triangles.append(get_triangle())
        mesh.shade_ids.append(i)

    mesh.vert_infs[0].bone_inf = 0.0

    mesh.mat_info = get_material_info()
    mesh.material_pass = get_material_pass()
    mesh.aabbtree = get_aabbtree()

    for _ in range(3):
        mesh.shaders.append(get_shader())
        mesh.vert_materials.append(get_vertex_material())
        mesh.textures.append(get_texture())
        mesh.shader_materials.append(get_shader_material())
    return mesh


def compare_lists(self, expected, actual):
    self.assertEqual(len(expected), len(actual))
    self.assertEqual(expected, actual)


def compare_meshes(self, expected, actual):
    compare_mesh_headers(self, expected.header, actual.header)
    compare_lists(self, expected.verts, actual.verts)
    compare_lists(self, expected.normals, actual.normals)
    compare_lists(self, expected.shade_ids, actual.shade_ids)

    self.assertEqual(len(expected.vert_infs), len(actual.vert_infs))
    for i in range(len(expected.vert_infs)):
        compare_vertex_influences(self, expected.vert_infs[i], actual.vert_infs[i])

    self.assertEqual(len(expected.triangles), len(actual.triangles))
    for i in range(len(expected.triangles)):
        compare_triangles(self, expected.triangles[i], actual.triangles[i])

    self.assertEqual(len(expected.shaders), len(actual.shaders))
    for i in range(len(expected.shaders)):
        compare_shaders(self, expected.shaders[i], actual.shaders[i])

    self.assertEqual(len(expected.vert_materials), len(actual.vert_materials))
    for i in range(len(expected.vert_materials)):
        compare_vertex_materials(self, expected.vert_materials[i], actual.vert_materials[i])

    self.assertEqual(len(expected.textures), len(actual.textures))
    for i in range(len(expected.textures)):
        compare_textures(self, expected.textures[i], actual.textures[i])

    self.assertEqual(len(expected.shader_materials), len(actual.shader_materials))
    for i in range(len(expected.shader_materials)):
        compare_shader_materials(self, expected.shader_materials[i], actual.shader_materials[i])