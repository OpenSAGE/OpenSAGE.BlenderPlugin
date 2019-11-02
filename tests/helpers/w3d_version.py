# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from io_mesh_w3d.structs.w3d_version import Version


def get_version():
    return Version(major=5, minor=0)


def compare_versions(self, expected, actual):
    self.assertEqual(expected.major, actual.major)
    self.assertEqual(expected.minor, actual.minor)
