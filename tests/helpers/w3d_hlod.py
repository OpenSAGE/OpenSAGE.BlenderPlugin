# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest

from io_mesh_w3d.structs.w3d_hlod import HLod, HLodHeader, HLodArray, HLodArrayHeader, HLodSubObject

from tests.helpers.w3d_version import get_version, compare_versions


def get_hlod_header(model_name, hierarchy_name):
    return HLodHeader(
        version=get_version(),
        lod_count=1,
        model_name=model_name,
        hierarchy_name=hierarchy_name)


def compare_hlod_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.lod_count, actual.lod_count)
    self.assertEqual(expected.model_name, actual.model_name)
    self.assertEqual(expected.hierarchy_name, actual.hierarchy_name)


def get_hlod_array_header():
    return HLodArrayHeader(
        model_count=0,
        max_screen_size=0.0)


def compare_hlod_array_headers(self, expected, actual):
    self.assertEqual(expected.model_count, actual.model_count)
    self.assertEqual(expected.max_screen_size, actual.max_screen_size)


def get_hlod_sub_object(bone, name):
    return HLodSubObject(
        bone_index=bone,
        name=name)


def compare_hlod_sub_objects(self, expected, actual):
    self.assertEqual(expected.bone_index, actual.bone_index)
    self.assertEqual(expected.name, actual.name)


def get_hlod_array():
    array = HLodArray(
        header=get_hlod_array_header(),
        sub_objects=[])

    array.sub_objects.append(get_hlod_sub_object(
        bone=0, name="containerName.BOUNDINGBOX"))
    array.sub_objects.append(get_hlod_sub_object(
        bone=5, name="containerName.sword"))
    array.sub_objects.append(get_hlod_sub_object(
        bone=0, name="containerName.soldier"))
    array.sub_objects.append(get_hlod_sub_object(
        bone=6, name="containerName.shield"))

    array.header.model_count = len(array.sub_objects)
    return array


def get_hlod_array_minimal():
    array = HLodArray(
        header=get_hlod_array_header(),
        sub_objects=[])

    array.sub_objects.append(get_hlod_sub_object(
        bone=0, name="containerName.BOUNDINGBOX"))

    array.header.model_count = len(array.sub_objects)
    return array


def compare_hlod_arrays(self, expected, actual):
    compare_hlod_array_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.sub_objects), len(actual.sub_objects))
    for i in range(len(expected.sub_objects)):
        compare_hlod_sub_objects(
            self, expected.sub_objects[i], actual.sub_objects[i])


def get_hlod(model_name="containerName", hierarchy_name="TestHierarchy"):
    return HLod(
        header=get_hlod_header(model_name, hierarchy_name),
        lod_array=get_hlod_array())


def get_hlod_minimal():
    return HLod(
        header=get_hlod_header("model_name", "hierarchy_name"),
        lod_array=get_hlod_array_minimal())


def compare_hlods(self, expected, actual):
    compare_hlod_headers(self, expected.header, actual.header)
    compare_hlod_arrays(self, expected.lod_array, actual.lod_array)
