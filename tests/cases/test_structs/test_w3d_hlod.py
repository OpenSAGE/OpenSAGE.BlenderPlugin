# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from io_mesh_w3d.structs.w3d_hlod import HLod, HLodHeader, HLodArray, HLodArrayHeader, HLodSubObject, W3D_CHUNK_HLOD
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.io_binary import read_chunk_head


class TestHLod(unittest.TestCase):
    def test_write_read(self):
        expected = HLod()
        expected.header = HLodHeader(
            version=Version(major=3, minor=2),
            lod_count=3,
            model_name="TestModelName",
            hierarchy_name="TestHieraName")
        expected.lod_array = HLodArray()

        self.assertEqual(40, expected.header.size_in_bytes())

        expected.lod_array.header = HLodArrayHeader(
            model_count=2,
            max_screen_size=5442)

        self.assertEqual(8, expected.lod_array.header.size_in_bytes())

        sub_object1 = HLodSubObject(
            bone_index=3,
            name="SubObjectNumber1")

        self.assertEqual(36, sub_object1.size_in_bytes())

        sub_object2 = HLodSubObject(
            bone_index=44,
            name="SubObjectNumber2")

        self.assertEqual(36, sub_object2.size_in_bytes())

        expected.lod_array.sub_objects.append(sub_object1)
        expected.lod_array.sub_objects.append(sub_object2)

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_HLOD, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = HLod.read(self, io_stream, chunkEnd)
        self.assertEqual(Version(major=3, minor=2), actual.header.version)
        self.assertEqual(3, actual.header.lod_count)
        self.assertEqual("TestModelName", actual.header.model_name)
        self.assertEqual("TestHieraName", actual.header.hierarchy_name)

        self.assertEqual(2, actual.lod_array.header.model_count)
        self.assertEqual(5442, actual.lod_array.header.max_screen_size)

        self.assertEqual(2, len(actual.lod_array.sub_objects))

        self.assertEqual(3, actual.lod_array.sub_objects[0].bone_index)
        self.assertEqual("SubObjectNumber1", actual.lod_array.sub_objects[0].name)

        self.assertEqual(44, actual.lod_array.sub_objects[1].bone_index)
        self.assertEqual("SubObjectNumber2", actual.lod_array.sub_objects[1].name)

