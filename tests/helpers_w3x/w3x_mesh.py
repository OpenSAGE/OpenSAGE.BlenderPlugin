# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from mathutils import Vector

from io_mesh_w3d.structs_w3x.w3x_mesh import *
from tests.helpers_w3x.w3x_fx_shader import *
from tests.helpers_w3x.w3x_aabbtree import *
from tests.utils import almost_equal


def get_triangle(vert_ids=[1, 2, 3],
                 normal=Vector((1.0, 22.0, -5.0)),
                 distance=103.0):
    return Triangle(
        vert_ids=vert_ids,
        normal=normal,
        distance=distance)


def compare_triangles(self, expected, actual):
    self.assertEqual(expected.vert_ids, actual.vert_ids)

    almost_equal(self, expected.normal[0], actual.normal[0], 0.2)
    almost_equal(self, expected.normal[1], actual.normal[1], 0.2)
    almost_equal(self, expected.normal[2], actual.normal[2], 0.2)

    almost_equal(self, expected.distance, actual.distance, 0.2)


def get_bounding_box():
    return BoundingBox(
        min=Vector((2.0, 3.10, 2.1)),
        max=Vector((4.0, 3.0, 2.0)))


def compare_bounding_boxes(self, expected, actual):
    almost_equal(self, expected.min[0], actual.min[0], 0.2)
    almost_equal(self, expected.min[1], actual.min[1], 0.2)
    almost_equal(self, expected.min[2], actual.min[2], 0.2)

    almost_equal(self, expected.max[0], actual.max[0], 0.2)
    almost_equal(self, expected.max[1], actual.max[1], 0.2)
    almost_equal(self, expected.max[2], actual.max[2], 0.2)


def get_bounding_sphere():
    return BoundingSphere(
        radius=3.13,
        center=Vector((3.0, 0.0, -1.0)))


def compare_bounding_spheres(self, expected, actual):
    almost_equal(self, expected.radius, actual.radius)

    almost_equal(self, expected.center[0], actual.center[0], 0.2)
    almost_equal(self, expected.center[1], actual.center[1], 0.2)
    almost_equal(self, expected.center[2], actual.center[2], 0.2)


def get_mesh():
    mesh = Mesh(
        id="MeshID",
        geometry_type="Normal",
        bounding_box=get_bounding_box(),
        bounding_sphere=get_bounding_sphere(),
        verts=[],
        normals=[],
        tangents=[],
        bitangents=[],
        tex_coords=[],
        shade_indices=[],
        triangles=[],
        fx_shader=get_fx_shader(),
        aabbtree=get_aabbtree())

    mesh.verts.append(Vector((1.0, 1.0, 1.0)))
    mesh.verts.append(Vector((1.0, 1.0, -1.0)))
    mesh.verts.append(Vector((1.0, -1.0, 1.0)))
    mesh.verts.append(Vector((1.0, -1.0, -1.0)))
    mesh.verts.append(Vector((-1.0, 1.0, 1.0)))
    mesh.verts.append(Vector((-1.0, 1.0, -1.0)))
    mesh.verts.append(Vector((-1.0, -1.0, 1.0)))
    mesh.verts.append(Vector((-1.0, -1.0, -1.0)))

    mesh.normals.append(Vector((0.577, 0.577, 0.577)))
    mesh.normals.append(Vector((0.577, 0.577, -0.577)))
    mesh.normals.append(Vector((0.577, -0.577, 0.577)))
    mesh.normals.append(Vector((0.577, -0.577, -0.577)))
    mesh.normals.append(Vector((-0.577, 0.577, 0.577)))
    mesh.normals.append(Vector((-0.577, 0.577, -0.577)))
    mesh.normals.append(Vector((-0.577, -0.577, 0.577)))
    mesh.normals.append(Vector((-0.577, -0.577, -0.577)))

    mesh.tangents.append(Vector((0.577, 0.577, 0.577)))
    mesh.tangents.append(Vector((0.577, 0.577, -0.577)))
    mesh.tangents.append(Vector((0.577, -0.577, 0.577)))
    mesh.tangents.append(Vector((0.577, -0.577, -0.577)))
    mesh.tangents.append(Vector((-0.577, 0.577, 0.577)))
    mesh.tangents.append(Vector((-0.577, 0.577, -0.577)))
    mesh.tangents.append(Vector((-0.577, -0.577, 0.577)))
    mesh.tangents.append(Vector((-0.577, -0.577, -0.577)))

    mesh.bitangents.append(Vector((0.577, 0.577, 0.577)))
    mesh.bitangents.append(Vector((0.577, 0.577, -0.577)))
    mesh.bitangents.append(Vector((0.577, -0.577, 0.577)))
    mesh.bitangents.append(Vector((0.577, -0.577, -0.577)))
    mesh.bitangents.append(Vector((-0.577, 0.577, 0.577)))
    mesh.bitangents.append(Vector((-0.577, 0.577, -0.577)))
    mesh.bitangents.append(Vector((-0.577, -0.577, 0.577)))
    mesh.bitangents.append(Vector((-0.577, -0.577, -0.577)))

    mesh.triangles.append(get_triangle(
        [4, 2, 0], Vector((0.0, 0.0, 1.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [2, 7, 3], Vector((0.0, -1.0, 0.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [6, 5, 7], Vector((-1.0, 0.0, 0.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [1, 7, 5], Vector((0.0, 0.0, -1.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [0, 3, 1], Vector((1.0, 0.0, 0.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [4, 1, 5], Vector((0.0, 1.0, 0.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [4, 6, 2], Vector((0.0, 0.0, 1.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [2, 6, 7], Vector((0.0, -1.0, 0.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [6, 4, 5], Vector((-1.0, 0.0, 0.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [1, 3, 7], Vector((0.0, 0.0, -1.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [0, 2, 3], Vector((1.0, 0.0, 0.0)), 0.63))
    mesh.triangles.append(get_triangle(
        [4, 0, 1], Vector((0.0, 1.0, 0.0)), 0.63))

    mesh.tex_coords.append(Vector((0.0, 0.1)))
    mesh.tex_coords.append(Vector((0.0, 0.4)))
    mesh.tex_coords.append(Vector((1.0, 0.6)))
    mesh.tex_coords.append(Vector((0.3, 0.1)))
    mesh.tex_coords.append(Vector((0.2, 0.2)))
    mesh.tex_coords.append(Vector((0.6, 0.6)))
    mesh.tex_coords.append(Vector((0.1, 0.8)))
    mesh.tex_coords.append(Vector((0.7, 0.7)))

    mesh.shade_indices = [1, 2, 3, 4, 5, 6, 7, 8]

    return mesh


def get_mesh_minimal():
    return Mesh(
        id="MeshID",
        geometry_type="Normal",
        bounding_box=get_bounding_box(),
        bounding_sphere=get_bounding_sphere(),
        verts=[Vector((1.0, 1.0, 1.0))],
        normals=[Vector((0.577, 0.577, 0.577))],
        tangents=[],
        bitangents=[],
        tex_coords=[Vector((0.0, 0.1))],
        shade_indices=[1],
        triangles=[get_triangle(
            [4, 2, 0], Vector((0.0, 0.0, 1.0)), 0.63)],
        fx_shader=get_fx_shader_minimal(),
        aabbtree=get_aabbtree_minimal())


def compare_meshes(self, expected, actual):
    self.assertEqual(expected.id, actual.id)
    self.assertEqual(expected.geometry_type, actual.geometry_type)

    compare_bounding_boxes(self, expected.bounding_box, actual.bounding_box)
    compare_bounding_spheres(self, expected.bounding_sphere, actual.bounding_sphere)

    self.assertEqual(len(expected.verts), len(actual.verts))
    for i, expect in enumerate(expected.verts):
        self.assertAlmostEqual(expect[0], actual.verts[i][0], 3)
        self.assertAlmostEqual(expect[1], actual.verts[i][1], 3)
        self.assertAlmostEqual(expect[2], actual.verts[i][2], 3)

    self.assertEqual(len(expected.normals), len(actual.normals))
    for i, expect in enumerate(expected.normals):
        self.assertAlmostEqual(expect[0], actual.normals[i][0], 3)
        self.assertAlmostEqual(expect[1], actual.normals[i][1], 3)
        self.assertAlmostEqual(expect[2], actual.normals[i][2], 3)

    self.assertEqual(len(expected.tangents), len(actual.tangents))
    self.assertEqual(len(expected.bitangents), len(actual.bitangents))

    self.assertEqual(len(expected.tex_coords), len(actual.tex_coords))
    for i, expect in enumerate(expected.tex_coords):
        self.assertAlmostEqual(expect[0], actual.tex_coords[i][0], 3)
        self.assertAlmostEqual(expect[1], actual.tex_coords[i][1], 3)

    self.assertEqual(len(expected.shade_indices), len(actual.shade_indices))
    self.assertEqual(expected.shade_indices, actual.shade_indices)

    self.assertEqual(len(expected.triangles), len(actual.triangles))
    for i, expect in enumerate(expected.triangles):
        compare_triangles(self, expect, actual.triangles[i])

    compare_fx_shaders(self, expected.fx_shader, actual.fx_shader)
    compare_aabbtrees(self, expected.aabbtree, actual.aabbtree)