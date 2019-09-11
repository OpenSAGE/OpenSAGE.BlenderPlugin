# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_material import VertexMaterial, VertexMaterialInfo, \
    MaterialInfo, MaterialPass, TextureStage, W3D_CHUNK_VERTEX_MATERIAL, \
    W3D_CHUNK_MATERIAL_PASS, W3D_CHUNK_TEXTURE_STAGE
from io_mesh_w3d.io_binary import read_chunk_head


class TestVertexMaterial(unittest.TestCase):
    def test_write_read(self):
        expected = VertexMaterial(
            vm_name="VM_NAME",
            vm_args_0="VM_ARGS0",
            vm_args_1="VM_ARGS1")
        expected.vm_info = VertexMaterialInfo(
            attributes=33,
            ambient=RGBA(r=3, g=1, b=44, a=3),
            diffuse=RGBA(r=12, g=4, b=33, a=46),
            specular=RGBA(r=99, g=244, b=255, a=255),
            emissive=RGBA(r=123, g=221, b=33, a=56),
            shininess=67.0,
            opacity=123.0,
            translucency=1335.0)

        self.assertEqual(32, expected.vm_info.size_in_bytes())
        self.assertEqual(90, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_VERTEX_MATERIAL, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = VertexMaterial.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.vm_name, actual.vm_name)
        self.assertEqual(expected.vm_args_0, actual.vm_args_0)
        self.assertEqual(expected.vm_args_1, actual.vm_args_1)

        self.assertEqual(expected.vm_info.attributes, actual.vm_info.attributes)
        self.assertEqual(expected.vm_info.ambient, actual.vm_info.ambient)
        self.assertEqual(expected.vm_info.diffuse, actual.vm_info.diffuse)
        self.assertEqual(expected.vm_info.specular, actual.vm_info.specular)
        self.assertEqual(expected.vm_info.emissive, actual.vm_info.emissive)
        self.assertEqual(expected.vm_info.shininess, actual.vm_info.shininess)
        self.assertEqual(expected.vm_info.opacity, actual.vm_info.opacity)
        self.assertEqual(expected.vm_info.translucency, actual.vm_info.translucency)


class TestMaterialInfo(unittest.TestCase):
    def test_write_read(self):
        expected = MaterialInfo(
            pass_count=33,
            vert_matl_count=123,
            shader_count=43,
            texture_count=142)

        self.assertEqual(16, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = MaterialInfo.read(io_stream)

        self.assertEqual(expected.pass_count, actual.pass_count)
        self.assertEqual(expected.vert_matl_count, actual.vert_matl_count)
        self.assertEqual(expected.shader_count, actual.shader_count)
        self.assertEqual(expected.texture_count, actual.texture_count)


class TestMaterialPass(unittest.TestCase):
    def test_write_read(self):
        expected = MaterialPass(
            vertex_material_ids=[],
            shader_ids=[],
            dcg=[],
            dig=[],
            scg=[],
            shader_material_ids=[],
            tx_stages=[],
            tx_coords=[])

        for i in range(333):
            expected.vertex_material_ids.append(i)

        for i in range(331):
            expected.shader_ids.append(i)

        for _ in range(155):
            expected.dcg.append(RGBA(r=3, g=44, b=133, a=222))

        for _ in range(174):
            expected.dig.append(RGBA(r=3, g=44, b=133, a=222))

        for _ in range(129):
            expected.scg.append(RGBA(r=3, g=44, b=133, a=222))

        for i in range(174):
            expected.shader_material_ids.append(i)

        for i in range(32):
            expected.tx_coords.append((0.5, 0.7))

        tx_stage = TextureStage(
            tx_ids=[],
            per_face_tx_coords=[],
            tx_coords=[])
        
        for i in range(123):
            tx_stage.tx_ids.append(i)
        
        for _ in range(223):
            tx_stage.tx_coords.append((2, 4))

        for _ in range(66):
            tx_stage.per_face_tx_coords.append(Vector((33.0, -2.0, 1.0)))

        for _ in range(12):
            expected.tx_stages.append(tx_stage)

        self.assertEqual(42696, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_MATERIAL_PASS, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = MaterialPass.read(io_stream, chunkEnd)
        self.assertEqual(expected.vertex_material_ids, actual.vertex_material_ids)
        self.assertEqual(expected.shader_ids, actual.shader_ids)
        self.assertEqual(expected.dcg, actual.dcg)
        self.assertEqual(expected.dig, actual.dig)
        self.assertEqual(expected.scg, actual.scg)
        self.assertEqual(expected.shader_material_ids, actual.shader_material_ids)

        for i, tx_coord in enumerate(expected.tx_coords):
            self.assertAlmostEqual(tx_coord[0], actual.tx_coords[i][0], 5)
            self.assertAlmostEqual(tx_coord[1], actual.tx_coords[i][1], 5)

        for i, stage in enumerate(expected.tx_stages):
            act = actual.tx_stages[i]
            for j, tx_id in enumerate(stage.tx_ids):
                self.assertEqual(tx_id, act.tx_ids[j])
            for j, tx_coord in enumerate(stage.tx_coords):
                self.assertAlmostEqual(tx_coord, act.tx_coords[j], 5)
            for j, tx_id in enumerate(stage.per_face_tx_coords):
                self.assertAlmostEqual(tx_id, act.per_face_tx_coords[j], 5)



class TestTextureStage(unittest.TestCase):
    def test_write_read(self):
        expected = TextureStage(
            tx_ids=[],
            per_face_tx_coords=[],
            tx_coords=[])
        
        for i in range(123):
            expected.tx_ids.append(i)
        
        for i in range(223):
            expected.tx_coords.append((2, 4))

        for i in range(66):
            expected.per_face_tx_coords.append(Vector((33.0, -2.0, 1.0)))
        
        self.assertEqual(3092, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_TEXTURE_STAGE, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = TextureStage.read(io_stream, chunkEnd)
        self.assertEqual(expected.tx_ids, actual.tx_ids)
        self.assertEqual(expected.per_face_tx_coords, actual.per_face_tx_coords)
        self.assertEqual(expected.tx_coords, actual.tx_coords)