# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import sys
import random
from enum import IntEnum
from io_mesh_w3d.common.structs.mesh_structs.aabbtree import *


COINCIDENCE_EPSILON = 0.001
WWMATH_EPSILON = 0.0001


class AxisEnum(IntEnum):
    XNORMAL = 0,
    YNORMAL = 1,
    ZNORMAL = 2


class OverlapType(IntEnum):
    NONE = 0x00,
    POS = 0x01,
    NEG = 0x02,
    ON = 0x04,
    BOTH = 0x08,
    OUTSIDE = POS,
    INSIDE = NEG,
    OVERLAPPED = BOTH,
    FRONT = POS,
    BACK = NEG


class AAPlaneClass(Struct): 
    normal = AxisEnum.XNORMAL
    dist = 0.0


MIN_POLYS_PER_NODE = 4

class CullNodeStruct(Struct):
    triangle_indices = []
    front = None
    back = None
    min = Vector((0, 0, 0))
    max = Vector((0, 0, 0))
    index = 0


class SplitChoiceStruct(Struct):
    cost = 0.0
    front_count = 0
    back_count = 0
    bmin = Vector((0, 0, 0))
    bmax = Vector((0, 0, 0))
    fmin = Vector((0, 0, 0))
    fmax = Vector((0, 0, 0))
    plane = None


class SplitArraysStruct(Struct):
    front_triangles = []
    back_triangles = []




class AABBTreeCreator():
    triangles = []
    verices = []


    def create(self, triangles, vertices):
        self.triangles = triangles
        self.vertices = vertices

        result = AABBTree(
            header=AABBTreeHeader(),
            poly_indices=[],
            nodes=[])

        root = AABBTreeNode(
            min=min,
            max=max,
            polys=None,
            children=None)

        triangle_ids = []
        for i in range(len(triangles)):
            triangle_ids.append(i)
        self.build_tree(root, triangle_ids)


    def build_tree(self, node, triangle_ids=[]):
        triangle_count = len(triangle_ids)

        if triangle_count <= MIN_POLYS_PER_NODE:
            node.poly_indices = triangle_ids
            return

        sc = self.select_splitting_plane(triangle_ids)
        if (sc.front_count + sc.back_count != triangle_count):
            node.poly_indices = triangle_ids
            return;
    
        arrays = SplitArraysStruct()
        split_polys(triangle_ids, sc, arrays)

        if arrays.front_triangles:
            node.front = AABBTreeNode(
                min=Vector((0, 0, 0)),
                max=Vector((0, 0, 0)),
                polys=None,
                children=None)
            self.build_tree(node.front, arrays.front_triangles)
        if arrays.back_triangles:
            node.back = AABBTreeNode(
                min=Vector((0, 0, 0)),
                max=Vector((0, 0, 0)),
                polys=None,
                children=None)
            build_tree(node.Back,arrays.back_triangles)


    def select_splitting_plane(self, triangle_ids):
        MAX_NUM_TRYS = 50
        triangle_count = len(triangle_ids)
        num_trys = min(MAX_NUM_TRYS, triangle_count)

        best_plane_stats = SplitChoiceStruct()
        for trys in range(num_trys):
            plane = AAPlaneClass()
            triangle_index = triangle_ids[random.randint(0, triangle_count - 1)]
            triangle = self.triangles[triangle_index]
            vertex = self.vertices[triangle.vert_ids[random.randint(0, 2)]]

            ran = random.randint(0, 2)
            if ran == 0:
                plane.normal = AxisEnum.XNORMAL
                plane.dist = vertex.x
            elif ran == 1:
                plane.normal = AxisEnum.YNORMAL
                plane.dist = vertex.y
            elif ran == 2:
                plane.normal = AxisEnum.ZNORMAL
                plane.dist = vertex.z

            considered_plane_stats = self.compute_plane_score(triangle_ids, plane);
            if considered_plane_stats.cost < best_plane_stats.cost:
                best_plane_stats = considered_plane_stats
        return best_plane_stats


    def compute_plane_score(self, triangle_ids, plane):
        sc = SplitChoiceStruct()
        sc.plane = plane

        for triangle_index in triangle_ids:
            side = self.which_side(plane, triangle_index)
            if side == OverlapType.FRONT or side == OverlapType.ON or side == OverlapType.BOTH:
                ++sc.front_count
                self.update_min_max(triangle_index, sc.fmin, sc.fmax)
            elif side == OverlapType.BACK:
                ++sc.back_count;
                self.update_min_max(poly_index, sc.bmin,sc.bmax)

        sc.bmin -= Vector((WWMATH_EPSILON, WWMATH_EPSILON, WWMATH_EPSILON))
        sc.bmax += Vector((WWMATH_EPSILON, WWMATH_EPSILON, WWMATH_EPSILON))

        if (sc.front_count == 0) or (sc.back_count == 0):
            sc.cost = sys.float_info.max
        else:
            back_cost = (sc.bmax.X - sc.bmin.X) * (sc.bmax.Y - sc.bmin.Y) * (sc.bmax.Z - sc.bmin.Z) * sc.back_count
            front_cost = (sc.fmax.X - sc.fmin.X) * (sc.fmax.Y - sc.fmin.Y) * (sc.fmax.Z - sc.fmin.Z) * sc.front_count
            sc.cost = front_cost + back_cost
        return sc


    def which_side(self, plane, triangle_index):
        mask = OverlapType.NONE
        triangle = self.triangles[triangle_index]
        for vert_index in triangle.vert_ids:
            point = self.vertices[vert_index]
            delta = point[plane.normal] - plane.dist
            if delta > COINCIDENCE_EPSILON:
                mask |= OverlapType.POS
            if delta < -COINCIDENCE_EPSILON:
                mask |= OverlapType.NEG
            mask |= OverlapType.ON

        if mask == OverlapType.ON:
            return OverlapType.ON
        if (mask & ~(OverlapType.POS | OverlapType.ON)) == 0:
            return OverlapType.POS
        if (mask & ~(OverlapType.NEG | OverlapType.ON)) == 0:
            return OverlapType.NEG
        return OverlapType.BOTH


    def split_triangles(self, triangle_indices, sc, arrays):
        # TT_ASSERT(sc.FrontCount + sc.BackCount == poly_indices.size());

        for triangle_index in triangle_indices:
            res = self.which_side(sc.plane, triangle_index)
            if res == OverlapType.FRONT or res == OverlapType.ON or res == OverlapType.BOTH:
                arrays.front_polys.append(poly_index)
            elif res == OverlapType.BACK:
                arrays.back_polys.append(poly_index)


    def update_min_max(self, triangle_index, min, max):
        triangle_verts = self.triangles[triangle_index].vert_ids
        for vert_index in triangle_verts:
            point = self.vertices[vert_index]
            if (point.x < min.x):
               min.x = point.x
            if (point.y < min.y):
               min.y = point.y
            if (point.z < min.z):
               min.z = point.Z
            if (point.x > max.x):
               max.x = point.x
            if (point.y > max.y):
               max.y = point.y
            if (point.z > max.z):
               max.z = point.z