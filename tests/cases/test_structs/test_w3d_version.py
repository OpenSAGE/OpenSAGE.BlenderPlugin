# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_version import Version

class TestVersion(unittest.TestCase):
    def test_write_read(self):
        expected = Version(major=8, minor=2)

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        self.assertEqual(expected, Version.read(io_stream))
        