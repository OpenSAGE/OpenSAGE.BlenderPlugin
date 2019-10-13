# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from mathutils import Vector
from io_mesh_w3d.structs.w3d_box import Box
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.structs.w3d_version import Version

def get_box():
    return Box(
        version=Version(major=5, minor=22),
        box_type=3,
        collision_types=64,
        name="TestBoxxx",
        color=RGBA(r=125, g=110, b=55, a=244),
        center=Vector((1.0, 2.0, 3.0)),
        extend=Vector((4.0, 5.0, 6.0)))

def compare_boxes(self, expected, actual):
    self.assertEqual(expected.version.major, actual.version.major)
    self.assertEqual(expected.version.minor, actual.version.minor)
    self.assertEqual(expected.box_type, actual.box_type)
    self.assertEqual(expected.collision_types, actual.collision_types)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.color, actual.color)

    self.assertEqual(expected.center.x, actual.center.x)
    self.assertEqual(expected.center.y, actual.center.y)
    self.assertEqual(expected.center.z, actual.center.z)

    self.assertEqual(expected.extend.x, actual.extend.x)
    self.assertEqual(expected.extend.y, actual.extend.y)
    self.assertEqual(expected.extend.z, actual.extend.z)
