# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector, Quaternion

def get_vector(x=0.0, y=0.0, z=0.0):
    vec = Vector((0, 0, 0))
    vec.x = x
    vec.y = y
    vec.z = z
    return vec


def compare_vectors(self, expected, actual):
    self.assertAlmostEqual(expected.x, actual.x, 1)
    self.assertAlmostEqual(expected.y, actual.y, 1)
    self.assertAlmostEqual(expected.z, actual.z, 1)


def get_vector2(x=0.0, y=0.0):
    vec = Vector((0, 0, 0))
    vec.x = x
    vec.y = y
    return vec


def compare_vectors2(self, expected, actual):
    self.assertAlmostEqual(expected.x, actual.x, 1)
    self.assertAlmostEqual(expected.y, actual.y, 1)


def get_quat(w=1.0, x=0.0, y=0.0, z=0.0):
    quat = Quaternion((0, 0, 0, 0))
    quat.w = w
    quat.x = x
    quat.y = y
    quat.z = z
    return quat


def compare_quats(self, expected, actual):
    self.assertAlmostEqual(expected.w, actual.w, 1)
    self.assertAlmostEqual(expected.x, actual.x, 1)
    self.assertAlmostEqual(expected.y, actual.y, 1)
    self.assertAlmostEqual(expected.z, actual.z, 1)

