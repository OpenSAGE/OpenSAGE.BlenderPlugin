# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.rgba import RGBA


def get_rgba(a=0):
    return RGBA(r=3, g=200, b=44, a=a)


def compare_rgbas(self, expected, actual, delta=0):
    self.assertTrue(abs(expected.r - actual.r) <= delta)
    self.assertTrue(abs(expected.g - actual.g) <= delta)
    self.assertTrue(abs(expected.b - actual.b) <= delta)
    self.assertTrue(abs(expected.a - actual.a) <= delta)
