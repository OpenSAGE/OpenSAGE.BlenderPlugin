# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from io_mesh_w3d.w3d.structs.rgba import RGBA


def get_rgba(a=0):
    return RGBA(r=3, g=200, b=44, a=a)


def compare_rgbas(self, expected, actual):
    self.assertEqual(expected.r, actual.r)
    self.assertEqual(expected.g, actual.g)
    self.assertEqual(expected.b, actual.b)
    self.assertEqual(expected.a, actual.a)
