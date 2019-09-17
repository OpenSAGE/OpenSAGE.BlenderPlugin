# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_mesh import Mesh, MeshHeader, W3D_CHUNK_MESH
from io_mesh_w3d.structs.w3d_material import MaterialInfo, MaterialPass
from io_mesh_w3d.structs.w3d_aabbtree import MeshAABBTree
from io_mesh_w3d.io_binary import read_chunk_head

class TestMesh(unittest.TestCase):
    def test_write_read(self):
        expected = Mesh(
            header=MeshHeader(),
            user_text="TestUserText",
            verts=[],
            normals=[],
            vert_infs=[],
            triangles=[],
            shade_ids=[],
            mat_info=MaterialInfo(),
            shaders=[],
            vert_materials=[],
            textures=[],
            shader_materials=[],
            material_pass=MaterialPass(),
            aabbtree=MeshAABBTree())

        self.assertEqual(116, expected.header.size_in_bytes())

        expected.verts = get_vertices(3321)
        expected.normals = get_vertices(3321)



        self.assertEqual(79980, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size_in_bytes(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)


    def test_write_read_minimal(self):
        expected = Mesh(
            header=MeshHeader(),
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

        self.assertEqual(116, expected.header.size_in_bytes())
        self.assertEqual(148, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size_in_bytes(), chunk_size)

        actual = Mesh.read(self, io_stream, subchunk_end)
        self.assertEqual(expected.header.version, actual.header.version)
        self.assertEqual(expected.header.attrs, actual.header.attrs)
        self.assertEqual(expected.header.mesh_name, actual.header.mesh_name)
        self.assertEqual(expected.header.container_name, actual.header.container_name)
        self.assertEqual(expected.header.face_count, actual.header.face_count)
        self.assertEqual(expected.header.vert_count, actual.header.vert_count)
        self.assertEqual(expected.header.matl_count, actual.header.matl_count)
        self.assertEqual(expected.header.damage_stage_count, actual.header.damage_stage_count)
        self.assertEqual(expected.header.sort_level, actual.header.sort_level)
        self.assertEqual(expected.header.prelit_version, actual.header.prelit_version)
        self.assertEqual(expected.header.future_count, actual.header.future_count)
        self.assertEqual(expected.header.vert_channel_flags, actual.header.vert_channel_flags)
        self.assertEqual(expected.header.face_channel_falgs, actual.header.face_channel_falgs)
        self.assertEqual(expected.header.min_corner, actual.header.min_corner)
        self.assertEqual(expected.header.max_corner, actual.header.max_corner)
        self.assertEqual(expected.header.sph_center, actual.header.sph_center)
        self.assertEqual(expected.header.sph_radius, actual.header.sph_radius)

        self.compare_list(expected.verts, actual.verts)
        self.compare_list(expected.normals, actual.normals)
        self.compare_list(expected.vert_infs, actual.vert_infs)
        self.compare_list(expected.triangles, actual.triangles)
        self.compare_list(expected.shade_ids, actual.shade_ids)

        self.assertEqual(expected.mat_info, actual.mat_info)
        self.assertEqual(len(expected.shaders), len(actual.shaders))
        self.assertEqual(len(expected.vert_materials), len(actual.vert_materials))
        self.assertEqual(len(expected.textures), len(actual.textures))
        self.assertEqual(len(expected.shader_materials), len(actual.shader_materials))
        self.assertEqual(expected.material_pass, actual.material_pass)
        self.assertEqual(expected.aabbtree, actual.aabbtree)

    def compare_list(self, expected, actual):
        self.assertEqual(len(expected), len(actual))
        self.assertEqual(expected, actual)


def get_vertices(count):
    result = []
    for _ in range(count):
        result.append(Vector((0.0, 2.0, -1.2)))
    return result