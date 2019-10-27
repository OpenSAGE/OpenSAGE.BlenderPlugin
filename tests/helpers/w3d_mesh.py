# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from mathutils import Vector

from io_mesh_w3d.structs.w3d_mesh import Mesh, MeshHeader, GEOMETRY_TYPE_SKIN
from io_mesh_w3d.structs.w3d_triangle import Triangle
from io_mesh_w3d.structs.w3d_vertex_influence import VertexInfluence
from tests.helpers.w3d_material import *
from tests.helpers.w3d_shader import get_shader, compare_shaders
from tests.helpers.w3d_texture import get_texture, compare_textures
from tests.helpers.w3d_shader_material import get_shader_material, compare_shader_materials
from tests.helpers.w3d_aabbtree import get_aabbtree, compare_aabbtrees
from tests.helpers.w3d_triangle import compare_triangles
from tests.helpers.w3d_vertex_influence import get_vertex_influence, compare_vertex_influences
from tests.helpers.w3d_version import get_version, compare_versions


def get_mesh_header(name, skin):
    header = MeshHeader(
        version=get_version(),
        attrs=0,
        mesh_name=name,
        container_name="containerName",
        face_count=0,
        vert_count=0,
        matl_count=0,
        damage_stage_count=0,
        sort_level=0,
        prelit_version=0,
        future_count=0,
        vert_channel_flags=3,
        face_channel_flags=1,
        min_corner=Vector((-1.0, -1.0, -1.0)),
        max_corner=Vector((1.0, 1.0, 1.0)),
        sph_center=Vector((0.0, 0.0, 0.0)),
        sph_radius=0.0)

    if skin:
        header.attrs = GEOMETRY_TYPE_SKIN
    return header


def compare_mesh_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
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


def get_mesh(name="meshName", skin=False, minimal=False, shader_mats=False):
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
        material_passes=[],
        aabbtree=None)

    if minimal:
        return mesh

    mesh.user_text = "TestUserText"

    mesh.verts.append(Vector((1.0, 1.0, 1.0)))
    mesh.verts.append(Vector((1.0, 1.0, -1.0)))
    mesh.verts.append(Vector((1.0, -1.0, 1.0)))
    mesh.verts.append(Vector((1.0, -1.0, -1.0)))
    mesh.verts.append(Vector((-1.0, 1.0, 1.0)))
    mesh.verts.append(Vector((-1.0, 1.0, -1.0)))
    mesh.verts.append(Vector((-1.0, -1.0, 1.0)))
    mesh.verts.append(Vector((-1.0, -1.0, -1.0)))

    mesh.normals.append(Vector((0.5, 0.5, 0.5)))
    mesh.normals.append(Vector((0.5, 0.5, -0.5)))
    mesh.normals.append(Vector((0.5, -0.5, 0.5)))
    mesh.normals.append(Vector((0.5, -0.5, -0.5)))
    mesh.normals.append(Vector((-0.5, 0.5, 0.5)))
    mesh.normals.append(Vector((-0.5, 0.5, -0.5)))
    mesh.normals.append(Vector((-0.5, -0.5, 0.5)))
    mesh.normals.append(Vector((-0.5, -0.5, -0.5)))

    mesh.triangles.append(Triangle(vert_ids=(4, 2, 0), surface_type=13, normal=Vector((0.0, 0.0, 1.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(2, 7, 3), surface_type=13, normal=Vector((0.0, -1.0, 0.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(6, 5, 7), surface_type=13, normal=Vector((-1.0, 0.0, 0.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(1, 7, 5), surface_type=13, normal=Vector((0.0, 0.0, -1.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(0, 3, 1), surface_type=13, normal=Vector((1.0, 0.0, 0.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(4, 1, 5), surface_type=13, normal=Vector((0.0, 1.0, 0.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(4, 6, 2), surface_type=13, normal=Vector((0.0, 0.0, 1.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(2, 6, 7), surface_type=13, normal=Vector((0.0, -1.0, 0.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(6, 4, 5), surface_type=13, normal=Vector((-1.0, 0.0, 0.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(1, 3, 7), surface_type=13, normal=Vector((0.0, 0.0, -1.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(0, 2, 3), surface_type=13, normal=Vector((1.0, 0.0, 0.0)), distance=1.1))
    mesh.triangles.append(Triangle(vert_ids=(4, 0, 1), surface_type=13, normal=Vector((0.0, 1.0, 0.0)), distance=1.1))

    if skin:
        mesh.vert_infs.append(VertexInfluence(bone_idx=1, xtra_idx=0, bone_inf=0.0, xtra_inf=0.0))
        mesh.vert_infs.append(VertexInfluence(bone_idx=1, xtra_idx=0, bone_inf=0.0, xtra_inf=0.0))
        mesh.vert_infs.append(VertexInfluence(bone_idx=2, xtra_idx=1, bone_inf=75.0, xtra_inf=25.0))
        mesh.vert_infs.append(VertexInfluence(bone_idx=2, xtra_idx=1, bone_inf=75.0, xtra_inf=25.0))
        mesh.vert_infs.append(VertexInfluence(bone_idx=3, xtra_idx=2, bone_inf=50.0, xtra_inf=50.0))
        mesh.vert_infs.append(VertexInfluence(bone_idx=3, xtra_idx=2, bone_inf=50.0, xtra_inf=50.0))
        mesh.vert_infs.append(VertexInfluence(bone_idx=4, xtra_idx=3, bone_inf=25.0, xtra_inf=75.0))
        mesh.vert_infs.append(VertexInfluence(bone_idx=4, xtra_idx=3, bone_inf=25.0, xtra_inf=75.0))

    for i, _ in enumerate(mesh.verts):
        mesh.shade_ids.append(i)

    mesh.aabbtree = get_aabbtree()

    for _ in range(2):
        mesh.shaders.append(get_shader())
        if shader_mats:
            mesh.shader_materials.append(get_shader_material())
        else:
            mesh.vert_materials.append(get_vertex_material())
        mesh.material_passes.append(get_material_pass())

    if not shader_mats:
        mesh.textures.append(get_texture()) #only one texture per material supported

    mesh.mat_info = MaterialInfo(
        pass_count=len(mesh.material_passes), 
        vert_matl_count=len(mesh.vert_materials), 
        shader_count=len(mesh.shaders), 
        texture_count=len(mesh.textures))
    mesh.header.face_count = len(mesh.triangles)
    mesh.header.vert_count = len(mesh.verts)
    mesh.header.matl_count = len(mesh.vert_materials)
    return mesh


def compare_meshes(self, expected, actual, comp_normals=True):
    compare_mesh_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.verts), len(actual.verts))
    for i, expect in enumerate(expected.verts):
        self.assertAlmostEqual(expect[0], actual.verts[i][0])
        self.assertAlmostEqual(expect[1], actual.verts[i][1])
        self.assertAlmostEqual(expect[2], actual.verts[i][2])

    self.assertEqual(len(expected.normals), len(actual.normals))
    if comp_normals:
        for i, expect in enumerate(expected.normals):
            self.assertAlmostEqual(expect[0], actual.normals[i][0])
            self.assertAlmostEqual(expect[1], actual.normals[i][1])
            self.assertAlmostEqual(expect[2], actual.normals[i][2])

    self.assertEqual(len(expected.shade_ids), len(actual.shade_ids))
    for i, expect in enumerate(expected.shade_ids):
        self.assertAlmostEqual(expect, actual.shade_ids[i])

    #if expected.aabbtree is not None: #how to compute the aabbtree?
    if actual.aabbtree is not None:
        compare_aabbtrees(self, expected.aabbtree, actual.aabbtree)

    if expected.mat_info is not None:
        compare_material_infos(self, expected.mat_info, actual.mat_info)

    self.assertEqual(len(expected.material_passes), len(actual.material_passes))
    for i in range(len(expected.material_passes)):
        compare_material_passes(self, expected.material_passes[i], actual.material_passes[i])

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