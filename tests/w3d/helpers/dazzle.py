# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.dazzle import *


def get_dazzle(name='containerName.Brakelight', type='REN_BRAKELIGHT'):
    return Dazzle(
        name_=name,
        type_name=type)


def compare_dazzles(self, expected, actual):
    self.assertEqual(expected.name_, actual.name_)
    self.assertEqual(expected.type_name, actual.type_name)
