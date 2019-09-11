# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Vector, Quaternion

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_hierarchy import Hierarchy, HierarchyHeader, \
    HierarchyPivot, W3D_CHUNK_HIERARCHY
from io_mesh_w3d.io_binary import read_chunk_head


class TestHierarchy(unittest.TestCase):
    def test_write_read(self):
        expected = Hierarchy()
        expected.header = HierarchyHeader(
            version=Version(major=4, minor=1),
            name="HieraHeader",
            num_pivots=33,
            center_pos=Vector((2.0, 3.0, 1.0)))

        self.assertEqual(36, expected.header.size_in_bytes())

        pivot1 = HierarchyPivot(
            name="Roottransform",
            parent_id=-1,
            translation=Vector((22.0, 33.0, 1.0)),
            euler_angles=Vector((1.0, 12.0, -2.0)),
            rotation=Quaternion((1.0, -0.1, -0.2, -0.3)))

        self.assertEqual(60, pivot1.size_in_bytes())
        expected.pivots.append(pivot1)

        pivot2 = HierarchyPivot(
            name="Spine",
            parent_id=0,
            translation=Vector((-22.0, -33.0, -1.0)),
            euler_angles=Vector((-1.0, -12.0, 2.0)),
            rotation=Quaternion((-1.0, 0.1, 0.2, 0.3)))

        self.assertEqual(60, pivot2.size_in_bytes())
        expected.pivots.append(pivot2)

        for _ in range(64):
            expected.pivot_fixups.append(Vector((-1.0, -2.0, -3.0)))

        self.assertEqual(948, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HIERARCHY, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = Hierarchy.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.header.version, actual.header.version)
        self.assertEqual(expected.header.name, actual.header.name)
        self.assertEqual(expected.header.num_pivots, actual.header.num_pivots)
        self.assertEqual(expected.header.center_pos, actual.header.center_pos)

        self.assertEqual(len(expected.pivots), len(actual.pivots))

        for i, piv in enumerate(expected.pivots):
            act = actual.pivots[i]
            self.assertEqual(piv.name, act.name)
            self.assertEqual(piv.parent_id, act.parent_id)
            self.assertEqual(piv.translation, act.translation)
            self.assertEqual(piv.euler_angles, act.euler_angles)
            self.assertEqual(piv.rotation, act.rotation)

        self.assertEqual(len(expected.pivot_fixups), len(actual.pivot_fixups))

        for i, fix in enumerate(expected.pivot_fixups):
            self.assertEqual(fix, actual.pivot_fixups[i])
