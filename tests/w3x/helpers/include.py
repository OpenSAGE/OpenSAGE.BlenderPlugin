# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3x.structs.include import *


def get_include():
    return Include(
        type='type',
        source='source')


def compare_includes(self, expected, actual):
    self.assertEqual(expected.type, actual.type)
    self.assertEqual(expected.source, actual.source)
