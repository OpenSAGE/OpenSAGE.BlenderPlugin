# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_rgba import RGBA

class TestRGBA(unittest.TestCase):
    def test_write_read(self):
        expected = RGBA(r=244, g=123, b=33, a=99)

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        self.assertEqual(expected, RGBA.read(io_stream))

    def test_write_read_f(self):
        expected = RGBA(r=244, g=123, b=33, a=99)

        io_stream = io.BytesIO()
        expected.write_f(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        self.assertEqual(expected, RGBA.read_f(io_stream))
        