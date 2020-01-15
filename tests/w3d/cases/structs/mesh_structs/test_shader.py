# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.utils import TestCase
from tests.w3d.helpers.mesh_structs.shader import *


class TestShader(TestCase):
    def test_write_read(self):
        expected = get_shader()

        self.assertEqual(16, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = Shader.read(io_stream)
        compare_shaders(self, expected, actual)
