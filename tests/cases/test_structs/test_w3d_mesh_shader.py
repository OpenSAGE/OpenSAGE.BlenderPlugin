# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_mesh_shader import MeshShader

class TestMeshShader(unittest.TestCase):
    def test_write_read(self):
        expected = MeshShader(
            depth_compare=4,
            depth_mask=100,
            color_mask=44,
            dest_blend=6,
            fog_func=123,
            pri_gradient=90,
            sec_gradient=45,
            src_blend=42,
            texturing=11,
            detail_color_func=3,
            detail_alpha_func=7,
            shader_preset=8,
            alpha_test=83,
            post_detail_color_func=245,
            post_detail_alpha_func=32,
            pad=85)

        self.assertEqual(16, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = MeshShader.read(io_stream)

        self.assertEqual(4, actual.depth_compare)
        self.assertEqual(100, actual.depth_mask)
        self.assertEqual(44, actual.color_mask)
        self.assertEqual(6, actual.dest_blend)
        self.assertEqual(123, actual.fog_func)
        self.assertEqual(90, actual.pri_gradient)
        self.assertEqual(45, actual.sec_gradient)
        self.assertEqual(42, actual.src_blend)
        self.assertEqual(11, actual.texturing)
        self.assertEqual(3, actual.detail_color_func)
        self.assertEqual(7, actual.detail_alpha_func)

        self.assertEqual(8, actual.shader_preset)
        self.assertEqual(83, actual.alpha_test)
        self.assertEqual(245, actual.post_detail_color_func)
        self.assertEqual(32, actual.post_detail_alpha_func)
        self.assertEqual(85, actual.pad)

