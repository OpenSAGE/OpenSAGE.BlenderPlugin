# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.collision_box import *
from tests.mathutils import *
from tests.common.helpers.rgba import get_rgba, compare_rgbas
from tests.w3d.helpers.version import get_version, compare_versions


def get_collision_box(name='containerName.BOUNDINGBOX', xml=False):
    box = CollisionBox(
        version=get_version(),
        box_type=0,
        collision_types=0,
        name_=name,
        color=None,
        center=get_vec(1.0, 2.0, 3.0),
        extend=get_vec(4.0, 5.0, 6.0))

    if not xml:
        box.color = get_rgba()
    return box


def compare_collision_boxes(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.box_type, actual.box_type)
    self.assertEqual(expected.collision_types, actual.collision_types)
    self.assertEqual(expected.name_, actual.name_)
    if expected.color :
        compare_rgbas(self, expected.color, actual.color)
    compare_vectors(self, expected.center, actual.center)
    compare_vectors(self, expected.extend, actual.extend)
