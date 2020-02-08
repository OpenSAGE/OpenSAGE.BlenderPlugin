# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.mesh import *
from tests.utils import TestCase


def clear_tangents(mesh):
    mesh.tangents = []
    mesh.bitangents = []


class TestMesh(TestCase):
    def test_write_read(self):
        expected = get_mesh()

        self.assertEqual(3137, expected.size(False))
        self.assertEqual(3145, expected.size())

        self.write_read_test(expected, W3D_CHUNK_MESH, Mesh.read, compare_meshes, self, True)

    def test_write_read_variant2(self):
        expected = get_mesh(skin=True, shader_mats=True)

        self.assertEqual(4129, expected.size(False))
        self.assertEqual(4137, expected.size())

        self.write_read_test(expected, W3D_CHUNK_MESH, Mesh.read, compare_meshes, self, True, clear_tangents)

    def test_write_read_prelit(self):
        expected = get_mesh(prelit=True)

        self.assertEqual(5512, expected.size(False))
        self.assertEqual(5520, expected.size())

        self.write_read_test(expected, W3D_CHUNK_MESH, Mesh.read, compare_meshes, self, True)

    def test_write_read_empty(self):
        expected = get_mesh_empty()

        self.assertEqual(204, expected.size(False))
        self.assertEqual(212, expected.size())

        self.write_read_test(expected, W3D_CHUNK_MESH, Mesh.read, compare_meshes, self, True)

    def test_validate(self):
        mesh = get_mesh()
        self.file_format = 'W3D'
        self.assertTrue(mesh.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(mesh.validate(self))

        mesh.header.mesh_name = 'toooolongmeshname'
        self.file_format = 'W3D'
        self.assertFalse(mesh.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(mesh.validate(self))

    def test_chunk_order(self):
        expected_chunks = [
            W3D_CHUNK_MESH_HEADER,
            W3D_CHUNK_MESH_USER_TEXT,
            W3D_CHUNK_VERTICES,
            # vertices copies not used
            W3D_CHUNK_VERTEX_NORMALS,
            W3D_CHUNK_TANGENTS,
            W3D_CHUNK_BITANGENTS,
            # normals copies not used
            W3D_CHUNK_TRIANGLES,
            W3D_CHUNK_VERTEX_INFLUENCES,
            W3D_CHUNK_VERTEX_SHADE_INDICES,
            W3D_CHUNK_MATERIAL_INFO,
            W3D_CHUNK_VERTEX_MATERIALS,
            W3D_CHUNK_SHADERS,
            W3D_CHUNK_TEXTURES,
            W3D_CHUNK_SHADER_MATERIALS,
            W3D_CHUNK_MATERIAL_PASS]

        expected = get_mesh()
        expected.tangents = expected.normals
        expected.bitangents = expected.normals
        expected.vert_infs = get_vertex_influences()
        expected.shader_materials = [get_shader_material()]
        expected.shaders = [get_shader()]
        expected.vert_materials = [get_vertex_material()]
        expected.textures = [get_texture()]
        expected.material_passes = [get_material_pass()]

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)
        self.assertEqual(expected.size(False), chunk_size)

        for chunk in expected_chunks:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)
            self.assertEqual(hex(chunk), hex(chunk_type))
            io_stream.seek(chunk_size, 1)

    def test_unsupported_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_MESH, output, 54, has_sub_chunks=True)

        write_chunk_head(W3D_CHUNK_VERTICES_2, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)
        write_chunk_head(W3D_CHUNK_NORMALS_2, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)
        write_chunk_head(W3D_CHUNK_TANGENTS, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)
        write_chunk_head(W3D_CHUNK_BITANGENTS, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)
        write_chunk_head(W3D_CHUNK_DEFORM, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)
        write_chunk_head(W3D_CHUNK_PS2_SHADERS, output,
                         1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())

        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)

        self.warning = lambda text: self.assertEqual('unknown chunk_type in io_stream: 0x0', text)
        Mesh.read(self, io_stream, subchunk_end)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_MESH, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_MESH, chunk_type)

        Mesh.read(self, io_stream, subchunk_end)

    def test_chunk_sizes(self):
        mesh = get_mesh_minimal()

        self.assertEqual(116, mesh.header.size(False))
        self.assertEqual(124, mesh.header.size())

        self.assertEqual(5, text_size(mesh.user_text, False))

        self.assertEqual(12, vec_list_size(mesh.verts, False))

        self.assertEqual(12, vec_list_size(mesh.normals, False))

        self.assertEqual(12, vec_list_size(mesh.tangents, False))

        self.assertEqual(12, vec_list_size(mesh.bitangents, False))

        self.assertEqual(32, list_size(mesh.triangles, False))

        self.assertEqual(16, list_size(mesh.shaders, False))

        self.assertEqual(38, list_size(mesh.textures, False))

        self.assertEqual(4, long_list_size(mesh.shade_ids, False))

        self.assertEqual(240, list_size(mesh.shader_materials, False))

        self.assertEqual(292, list_size(mesh.material_passes, False))

        self.assertEqual(78, list_size(mesh.vert_materials, False))

        self.assertEqual(1105, mesh.size(False))
        self.assertEqual(1113, mesh.size())

    def test_write_read_xml(self):
        self.write_read_xml_test(get_mesh(shader_mats=True), 'W3DMesh', Mesh.parse, compare_meshes, self)

    def test_write_read_minimal_xml(self):
        self.write_read_xml_test(get_mesh_minimal(xml=True), 'W3DMesh', Mesh.parse, compare_meshes, self)

    def test_node_order(self):
        expecteds = ['BoundingBox',
                     'BoundingSphere',
                     'Vertices',
                     'Normals',
                     'Tangents',
                     'Binormals',
                     'TexCoords',
                     'BoneInfluences',
                     'BoneInfluences',
                     'ShadeIndices',
                     'Triangles',
                     'FXShader',
                     'AABTree']

        root = create_root()
        mesh = get_mesh(shader_mats=True, skin=True)
        mesh.create(root)

        for i, child in enumerate(root.find('W3DMesh')):
            self.assertEqual(expecteds[i], child.tag)
