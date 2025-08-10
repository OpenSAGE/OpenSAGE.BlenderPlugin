# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.mesh import *
from tests.common.helpers.mesh_structs.aabbtree import *
from tests.common.helpers.mesh_structs.shader_material import *
from tests.common.helpers.mesh_structs.triangle import *
from tests.common.helpers.mesh_structs.vertex_influence import *
from tests.w3d.helpers.mesh_structs.prelit import *
from tests.w3d.helpers.version import *


def get_mesh_header(name='mesh_name', skin=False, shader_mats=False, hidden=False, cast_shadow=False, two_sided=False):
    header = MeshHeader(
        version=get_version(major=4, minor=2),
        attrs=0,
        mesh_name=name,
        container_name='containerName',
        face_count=12,
        vert_count=8,
        matl_count=2,
        damage_stage_count=0,
        sort_level=3,
        prelit_version=0,
        future_count=0,
        vert_channel_flags=VERTEX_CHANNEL_LOCATION | VERTEX_CHANNEL_NORMAL,
        face_channel_flags=1,
        min_corner=get_vec(-1.0, -1.0, -1.0),
        max_corner=get_vec(1.0, 1.0, 1.0),
        sph_center=get_vec(0.0, 0.0, 0.0),
        sph_radius=0.0)

    if shader_mats:
        header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT | VERTEX_CHANNEL_BITANGENT
    if skin:
        header.attrs |= GEOMETRY_TYPE_SKIN
        header.vert_channel_flags |= VERTEX_CHANNEL_BONE_ID
    if hidden:
        header.attrs |= GEOMETRY_TYPE_HIDDEN
    if cast_shadow:
        header.attrs |= GEOMETRY_TYPE_CAST_SHADOW
    if two_sided:
        header.attrs |= GEOMETRY_TYPE_TWO_SIDED
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
    # compare_vectors(self, expected.min_corner, actual.min_corner)
    # compare_vectors(self, expected.max_corner, actual.max_corner)
    # compare_vectors(self, expected.sph_center, actual.sph_center)
    # self.assertAlmostEqual(expected.sph_radius, actual.sph_radius, 2)


def get_vertex_influences():
    return [get_vertex_influence(0, 0, 0.0, 0.0),
            get_vertex_influence(1, 0, 0.0, 0.0),
            get_vertex_influence(2, 1, 0.75, 0.25),
            get_vertex_influence(2, 1, 0.75, 0.25),
            get_vertex_influence(3, 2, 0.50, 0.50),
            get_vertex_influence(3, 2, 0.50, 0.50),
            get_vertex_influence(3, 4, 0.25, 0.75),
            get_vertex_influence(3, 4, 0.25, 0.75)]


def get_mesh(
        name='meshName',
        skin=False,
        shader_mats=False,
        prelit=False,
        hidden=False,
        cast_shadow=False,
        two_sided=False,
        mat_count=2):
    mesh = W3DMesh()
    mesh.header = get_mesh_header(name, skin, shader_mats, hidden, cast_shadow, two_sided)

    mesh.user_text = 'TestUserText'

    mesh.verts = [get_vec(1.0, 1.0, 1.0),
                  get_vec(1.0, 1.0, -1.0),
                  get_vec(1.0, -1.0, 1.0),
                  get_vec(1.0, -1.0, -1.0),
                  get_vec(-1.0, 1.0, 1.0),
                  get_vec(-1.0, 1.0, -1.0),
                  get_vec(-1.0, -1.0, 1.0),
                  get_vec(-1.0, -1.0, -1.0)]

    mesh.normals = [get_vec(0.577, 0.577, 0.577),
                    get_vec(0.577, 0.577, -0.577),
                    get_vec(0.577, -0.577, 0.577),
                    get_vec(0.577, -0.577, -0.577),
                    get_vec(-0.577, 0.577, 0.577),
                    get_vec(-0.577, 0.577, -0.577),
                    get_vec(-0.577, -0.577, 0.577),
                    get_vec(-0.577, -0.577, -0.577)]

    if shader_mats:
        mesh.tangents = [get_vec(0.577, 0.577, 0.577),
                         get_vec(0.577, 0.577, -0.577),
                         get_vec(0.577, -0.577, 0.577),
                         get_vec(0.577, -0.577, -0.577),
                         get_vec(-0.577, 0.577, 0.577),
                         get_vec(-0.577, 0.577, -0.577),
                         get_vec(-0.577, -0.577, 0.577),
                         get_vec(-0.577, -0.577, -0.577)]

        mesh.bitangents = [get_vec(0.577, 0.577, 0.577),
                           get_vec(0.577, 0.577, -0.577),
                           get_vec(0.577, -0.577, 0.577),
                           get_vec(0.577, -0.577, -0.577),
                           get_vec(-0.577, 0.577, 0.577),
                           get_vec(-0.577, 0.577, -0.577),
                           get_vec(-0.577, -0.577, 0.577),
                           get_vec(-0.577, -0.577, -0.577)]

    mesh.triangles = [get_triangle([4, 2, 0], 1, get_vec(0.0, 0.0, 1.0), 1.10),
                      get_triangle([2, 7, 3], 2, get_vec(0.0, -1.0, 0.0), 1.10),
                      get_triangle([6, 5, 7], 3, get_vec(-1.0, 0.0, 0.0), 1.10),
                      get_triangle([1, 7, 5], 4, get_vec(0.0, 0.0, -1.0), 1.10),
                      get_triangle([0, 3, 1], 5, get_vec(1.0, 0.0, 0.0), 1.10),
                      get_triangle([4, 1, 5], 6, get_vec(0.0, 1.0, 0.0), 1.10),
                      get_triangle([4, 6, 2], 7, get_vec(0.0, 0.0, 1.0), 1.10),
                      get_triangle([2, 6, 7], 8, get_vec(0.0, -1.0, 0.0), 1.10),
                      get_triangle([6, 4, 5], 9, get_vec(-1.0, 0.0, 0.0), 1.10),
                      get_triangle([1, 3, 7], 10, get_vec(0.0, 0.0, -1.0), 1.10),
                      get_triangle([0, 2, 3], 11, get_vec(1.0, 0.0, 0.0), 1.10),
                      get_triangle([4, 0, 1], 13, get_vec(0.0, 1.0, 0.0), 1.10)]

    if skin:
        mesh.multi_bone_skinned = True
        mesh.vert_infs = get_vertex_influences()
        # use same verts_2 as verts just for test
        mesh.verts_2 = [get_vec(1.0, 1.0, 1.0),
                        get_vec(1.0, 1.0, -1.0),
                        get_vec(1.0, -1.0, 1.0),
                        get_vec(1.0, -1.0, -1.0),
                        get_vec(-1.0, 1.0, 1.0),
                        get_vec(-1.0, 1.0, -1.0),
                        get_vec(-1.0, -1.0, 1.0),
                        get_vec(-1.0, -1.0, -1.0)]
        mesh.normals_2 = [get_vec(0.577, 0.577, 0.577),
                          get_vec(0.577, 0.577, -0.577),
                          get_vec(0.577, -0.577, 0.577),
                          get_vec(0.577, -0.577, -0.577),
                          get_vec(-0.577, 0.577, 0.577),
                          get_vec(-0.577, 0.577, -0.577),
                          get_vec(-0.577, -0.577, 0.577),
                          get_vec(-0.577, -0.577, -0.577)]

    for i in range(len(mesh.verts)):
        mesh.shade_ids.append(i)

    mesh.aabbtree = get_aabbtree()

    if shader_mats:
        mesh.shader_materials.append(get_shader_material())
        mesh.material_passes.append(get_material_pass(index=0, shader_mat=shader_mats))
    elif prelit:
        mesh.header.attrs |= PRELIT_UNLIT | PRELIT_VERTEX | PRELIT_LIGHTMAP_MULTI_PASS | PRELIT_LIGHTMAP_MULTI_TEXTURE
        mesh.prelit_unlit = get_prelit(type=W3D_CHUNK_PRELIT_UNLIT, count=1)
        mesh.prelit_vertex = get_prelit(type=W3D_CHUNK_PRELIT_VERTEX, count=1)
        mesh.prelit_lightmap_multi_pass = get_prelit(
            type=W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS, count=2)
        mesh.prelit_lightmap_multi_texture = get_prelit(
            type=W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE, count=2)
    else:
        for i in range(mat_count):
            mesh.shaders.append(get_shader())
            mesh.vert_materials.append(get_vertex_material())
            mesh.textures.append(get_texture())

            mesh.material_passes.append(get_material_pass(index=i, shader_mat=shader_mats))

    if not prelit:
        mesh.mat_info = get_material_info()
        mesh.mat_info.pass_count = len(mesh.material_passes)
        mesh.mat_info.vert_matl_count = len(mesh.vert_materials)
        mesh.mat_info.shader_count = len(mesh.shaders)
        mesh.mat_info.texture_count = len(mesh.textures)

    mesh.header.face_count = len(mesh.triangles)
    mesh.header.vert_count = len(mesh.verts)
    mesh.header.matl_count = max(len(mesh.vert_materials), len(mesh.shader_materials))
    return mesh


def get_mesh_two_textures(name='meshName'):
    mesh = get_mesh(name=name)

    mesh.shaders = [get_shader()]
    mesh.vert_materials = [get_vertex_material()]
    mesh.textures = [get_texture('texture.dds'), get_texture('texture2.dds')]
    mesh.material_passes = [get_material_pass(num_stages=2)]

    mesh.mat_info = get_material_info()
    mesh.mat_info.pass_count = len(mesh.material_passes)
    mesh.mat_info.vert_matl_count = len(mesh.vert_materials)
    mesh.mat_info.shader_count = len(mesh.shaders)
    mesh.mat_info.texture_count = len(mesh.textures)

    mesh.header.face_count = len(mesh.triangles)
    mesh.header.vert_count = len(mesh.verts)
    mesh.header.matl_count = len(mesh.vert_materials)
    return mesh


def get_mesh_minimal(xml=False):
    mesh = W3DMesh()
    mesh.header = get_mesh_header()
    mesh.user_text = 'text'
    mesh.verts = [get_vec()]
    mesh.normals = [get_vec()]
    mesh.tangents = [get_vec()]
    mesh.bitangents = [get_vec()]
    mesh.vert_infs = [get_vertex_influence()]
    mesh.triangles = [get_triangle()]
    mesh.shade_ids = [1]
    mesh.mat_info = get_material_info()
    mesh.shaders = [get_shader()]
    mesh.vert_materials = [get_vertex_material_minimal()]
    mesh.textures = [get_texture_minimal()]
    mesh.shader_materials = [get_shader_material_minimal()]
    mesh.material_passes = [get_material_pass_minimal()]
    mesh.aabbtree = get_aabbtree_minimal()
    mesh.prelit_unlit = None
    mesh.prelit_vertex = None
    mesh.prelit_lightmap_multi_pass = None
    mesh.prelit_lightmap_multi_texture = None

    mesh.mat_info.pass_count = 1
    mesh.mat_info.vert_mat_count = 1
    mesh.mat_info.shader_count = 1
    mesh.mat_info.texture_count = 1

    if xml:
        mesh.multi_bone_skinned = True
        mesh.header = get_mesh_header(shader_mats=True, skin=True)
        mesh.vert_materials = []
        mesh.header.matl_count = 1
        mesh.shaders = []
        mesh.textures = []
        mesh.mat_info.vert_mat_count = 0
        mesh.mat_info.shader_count = 0
        mesh.mat_info.texture_count = 0

        mesh.material_passes[0].vertex_material_ids = []
        mesh.material_passes[0].shader_ids = []
        mesh.material_passes[0].dcg = []
        mesh.material_passes[0].dig = []
        mesh.material_passes[0].scg = []
        mesh.material_passes[0].shader_material_ids = [0]
        mesh.material_passes[0].tx_stages = []

    mesh.header.face_count = 1
    mesh.header.vert_count = 1
    return mesh


def get_mesh_empty():
    mesh = W3DMesh()
    mesh.header = get_mesh_header()
    mesh.verts = [get_vec()]
    mesh.normals = [get_vec()]
    mesh.triangles = [get_triangle()]
    return mesh


def compare_meshes(self, expected, actual):
    compare_mesh_headers(self, expected.header, actual.header)

    is_skin = expected.is_skin()

    self.assertEqual(len(expected.verts), len(actual.verts))
    for i, expect in enumerate(expected.verts):
        compare_vectors(self, expect, actual.verts[i])

    self.assertEqual(len(expected.normals), len(actual.normals))
    if not is_skin:  # generated by blender if mesh is skinned/rigged
        for i, expect in enumerate(expected.normals):
            compare_vectors(self, expect, actual.normals[i])

    self.assertEqual(len(expected.tangents), len(actual.tangents))
    self.assertEqual(len(expected.bitangents), len(actual.bitangents))

    self.assertEqual(len(expected.shade_ids), len(actual.shade_ids))
    for i, expect in enumerate(expected.shade_ids):
        self.assertAlmostEqual(expect, actual.shade_ids[i])

    if expected.aabbtree is not None:
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
        compare_triangles(self, expected.triangles[i], actual.triangles[i], is_skin)

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

    if expected.prelit_unlit is not None:
        compare_prelits(self, expected.prelit_unlit, actual.prelit_unlit)
    if expected.prelit_vertex is not None:
        compare_prelits(self, expected.prelit_vertex, actual.prelit_vertex)
    if expected.prelit_lightmap_multi_pass is not None:
        compare_prelits(self, expected.prelit_lightmap_multi_pass, actual.prelit_lightmap_multi_pass)
    if expected.prelit_lightmap_multi_texture is not None:
        compare_prelits(self, expected.prelit_lightmap_multi_texture, actual.prelit_lightmap_multi_texture)
