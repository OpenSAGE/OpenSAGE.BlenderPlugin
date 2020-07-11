# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.version import Version


def get_version(major=5, minor=0):
    return Version(major=major, minor=minor)


def compare_versions(self, expected, actual):
    self.assertEqual(expected.major, actual.major)
    self.assertEqual(expected.minor, actual.minor)
