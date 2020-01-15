# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.utils import TestCase
from tests.w3d.helpers.version import *


class TestVersion(TestCase):
    def test_write_read(self):
        expected = get_version()

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        compare_versions(self, expected, Version.read(io_stream))

    def test_eq_true(self):
        ver = get_version()
        self.assertEqual(ver, ver)

    def test_eq_false(self):
        ver = get_version()
        other = Version(major=2, minor=1)

        self.assertNotEqual(ver, other)
        self.assertNotEqual(ver, 1)
        self.assertNotEqual(ver, "test")
