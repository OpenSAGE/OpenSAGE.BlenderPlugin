# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from tests.mathutils import *
from io_mesh_w3d.w3d.structs.box import Box
from io_mesh_w3d.w3d.structs.rgba import RGBA
from io_mesh_w3d.w3d.structs.version import Version

from tests.w3d.helpers.version import get_version, compare_versions
from tests.w3d.helpers.rgba import get_rgba, compare_rgbas


def get_box():
    return Box(
        version=get_version(),
        box_type=0,
        collision_types=0,
        name_="containerName.BOUNDINGBOX",
        color=get_rgba(),
        center=get_vector(1.0, 2.0, 3.0),
        extend=get_vector(4.0, 5.0, 6.0))


def compare_boxes(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.box_type, actual.box_type)
    self.assertEqual(expected.collision_types, actual.collision_types)
    self.assertEqual(expected.name_, actual.name_)
    compare_rgbas(self, expected.color, actual.color)

    compare_vectors(self, expected.center, actual.center)
    compare_vectors(self, expected.extend, actual.extend)
