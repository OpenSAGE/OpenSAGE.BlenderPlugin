# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from io_mesh_w3d.structs.w3d_version import Version


class TestVersion(TestCase):
    def test_write_read(self):
        expected = Version(major=8, minor=2)

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        self.assertEqual(expected, Version.read(io_stream))


    def test_eq_true(self):
        ver = Version(major=3, minor=1)
        self.assertEqual(ver, ver)


    def test_eq_false(self):
        ver = Version(major=4, minor=2)
        other = Version(major=2, minor=1)

        self.assertNotEqual(ver, other)
        self.assertNotEqual(ver, 1)
        self.assertNotEqual(ver, "test")
