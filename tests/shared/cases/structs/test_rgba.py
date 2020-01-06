# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.shared.helpers.rgba import *


class TestRGBA(TestCase):
    def test_write_read(self):
        expected = get_rgba()

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        compare_rgbas(self, expected, RGBA.read(io_stream))

    def test_write_read_f(self):
        expected = RGBA(r=244, g=123, b=33, a=99)

        io_stream = io.BytesIO()
        expected.write_f(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        compare_rgbas(self, expected, RGBA.read_f(io_stream))

    def test_eq_true(self):
        rgba = RGBA(r=244, g=222, b=1, a=0)
        self.assertEqual(rgba, rgba)

    def test_eq_false(self):
        rgba = RGBA(r=2, g=3, b=0, a=0)
        self.assertNotEqual(rgba, "test")
        self.assertNotEqual(rgba, 1)

    def test_to_string(self):
        rgba = RGBA(r=244, g=123, b=33, a=99)
        expected = "RGBA(r:244, g:123, b:33, a:99)"
        self.assertEqual(expected, str(rgba))
