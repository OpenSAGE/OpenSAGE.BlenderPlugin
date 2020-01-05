# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector, Quaternion, Matrix


def get_vec(x=0.0, y=0.0, z=0.0):
    vec = Vector((0, 0, 0))
    vec.x = x
    vec.y = y
    vec.z = z
    return vec


def compare_vectors(self, expected, actual):
    self.assertAlmostEqual(expected.x, actual.x, 1)
    self.assertAlmostEqual(expected.y, actual.y, 1)
    self.assertAlmostEqual(expected.z, actual.z, 1)


def get_vec2(x=0.0, y=0.0):
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


def get_mat(row0=None, row1=None, row2=None):
    mat = Matrix(([0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]))
    if row0 is not None:
        mat[0][0] = row0[0]
        mat[0][1] = row0[1]
        mat[0][2] = row0[2]
        mat[0][3] = row0[3]

    if row1 is not None:
        mat[1][0] = row1[0]
        mat[1][1] = row1[1]
        mat[1][2] = row1[2]
        mat[1][3] = row1[3]

    if row2 is not None:
        mat[2][0] = row2[0]
        mat[2][1] = row2[1]
        mat[2][2] = row2[2]
        mat[2][3] = row2[3]

    return mat


def compare_mats(self, expected, actual):
    self.assertAlmostEqual(expected[0][0], actual[0][0], 1)
    self.assertAlmostEqual(expected[0][1], actual[0][1], 1)
    self.assertAlmostEqual(expected[0][2], actual[0][2], 1)
    self.assertAlmostEqual(expected[0][3], actual[0][3], 1)

    self.assertAlmostEqual(expected[1][0], actual[1][0], 1)
    self.assertAlmostEqual(expected[1][1], actual[1][1], 1)
    self.assertAlmostEqual(expected[1][2], actual[1][2], 1)
    self.assertAlmostEqual(expected[1][3], actual[1][3], 1)

    self.assertAlmostEqual(expected[2][0], actual[2][0], 1)
    self.assertAlmostEqual(expected[2][1], actual[2][1], 1)
    self.assertAlmostEqual(expected[2][2], actual[2][2], 1)
    self.assertAlmostEqual(expected[2][3], actual[2][3], 1)
