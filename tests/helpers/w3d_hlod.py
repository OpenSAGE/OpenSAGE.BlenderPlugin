# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest

from io_mesh_w3d.structs.w3d_hlod import HLod, HLodHeader, HLodArray, HLodArrayHeader, HLodSubObject
from io_mesh_w3d.structs.w3d_version import Version

def get_hlod_header():
    return HLodHeader(
        version=Version(major=3, minor=2),
        lod_count=3,
        model_name="TestModelName",
        hierarchy_name="TestHieraName")

def compare_hlod_headers(self, expected, actual):
    self.assertEqual(expected.version, actual.version)
    self.assertEqual(expected.lod_count, actual.lod_count)
    self.assertEqual(expected.model_name, actual.model_name)
    self.assertEqual(expected.hierarchy_name, actual.hierarchy_name)

def get_hlod_array_header():
    return HLodArrayHeader(
        model_count=2,
        max_screen_size=5442)

def compare_hlod_array_headers(self, expected, actual):
    self.assertEqual(expected.model_count, actual.model_count)
    self.assertEqual(expected.max_screen_size, actual.max_screen_size)

def get_hlod_sub_object():
    return HLodSubObject(
        bone_index=3,
        name="SubObjectNumber1")

def compare_hlod_sub_objects(self, expected, actual):
    self.assertEqual(expected.bone_index, actual.bone_index)
    self.assertEqual(expected.name, actual.name)

def get_hlod_array(num_subobjects=2):
    array = HLodArray(
        header=get_hlod_array_header(),
        sub_objects=[])

    for _ in range(num_subobjects):
        array.sub_objects.append(get_hlod_sub_object())
    return array

def compare_hlod_arrays(self, expected, actual):
    compare_hlod_array_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.sub_objects), len(actual.sub_objects))
    for i in range(len(expected.sub_objects)):
        compare_hlod_sub_objects(self, expected.sub_objects[i], actual.sub_objects[i])


def get_hlod():
    return HLod(
        header=get_hlod_header(),
        lod_array=get_hlod_array())

def compare_hlods(self, expected, actual):
    compare_hlod_headers(self, expected.header, actual.header)
    compare_hlod_arrays(self, expected.lod_array, actual.lod_array)