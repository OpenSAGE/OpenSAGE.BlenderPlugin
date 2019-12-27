# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from io_mesh_w3d.structs.w3d_box import *
from tests.helpers.w3d_version import get_version, compare_versions
from tests.helpers.w3d_rgba import get_rgba, compare_rgbas


def get_box():
    return Box(
        version=get_version(),
        box_type=0,
        collision_types=0,
        name="containerName.BOUNDINGBOX",
        color=get_rgba(),
        center=Vector((1.0, 2.0, 3.0)),
        extend=Vector((4.0, 5.0, 6.0)))


def compare_boxes(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.box_type, actual.box_type)
    self.assertEqual(expected.collision_types, actual.collision_types)
    self.assertEqual(expected.name, actual.name)
    compare_rgbas(self, expected.color, actual.color)

    self.assertEqual(expected.center.x, actual.center.x)
    self.assertEqual(expected.center.y, actual.center.y)
    self.assertEqual(expected.center.z, actual.center.z)

    self.assertEqual(expected.extend.x, actual.extend.x)
    self.assertEqual(expected.extend.y, actual.extend.y)
    self.assertEqual(expected.extend.z, actual.extend.z)
