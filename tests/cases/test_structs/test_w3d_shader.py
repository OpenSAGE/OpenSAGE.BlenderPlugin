# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_shader import Shader
from tests.helpers.w3d_shader import get_shader, compare_shaders


class TestShader(unittest.TestCase):
    def test_write_read(self):
        expected = get_shader()

        self.assertEqual(16, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = Shader.read(io_stream)
        compare_shaders(self, expected, actual)
