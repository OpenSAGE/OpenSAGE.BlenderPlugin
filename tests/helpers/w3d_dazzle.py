# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from io_mesh_w3d.structs.w3d_dazzle import *


def get_dazzle():
    return Dazzle(
            name="Name",
            type_name="TypeName")


def compare_dazzles(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.type_name, actual.type_name)
