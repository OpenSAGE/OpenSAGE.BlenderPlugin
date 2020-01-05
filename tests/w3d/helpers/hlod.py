# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import sys
from io_mesh_w3d.w3d.structs.hlod import *
from tests.w3d.helpers.version import *

from io_mesh_w3d.w3d.structs.hlod import *

from tests.w3d.helpers.version import get_version, compare_versions


def get_hlod_header(model_name, hierarchy_name, lod_count=1):
    return HLodHeader(
        version=get_version(),
        lod_count=lod_count,
        model_name=model_name,
        hierarchy_name=hierarchy_name)


def compare_hlod_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.lod_count, actual.lod_count)
    self.assertEqual(expected.model_name, actual.model_name)
    self.assertEqual(expected.hierarchy_name, actual.hierarchy_name)


def get_hlod_array_header(count=0, size=0.0):
    return HLodArrayHeader(
        model_count=count,
        max_screen_size=size)


def compare_hlod_array_headers(self, expected, actual):
    self.assertEqual(expected.model_count, actual.model_count)
    self.assertAlmostEqual(expected.max_screen_size, actual.max_screen_size, 2)


def get_hlod_sub_object(bone, name):
    return HLodSubObject(
        bone_index=bone,
        name_=name)


def compare_hlod_sub_objects(self, expected, actual):
    self.assertEqual(expected.name_, actual.name_)
    self.assertEqual(expected.bone_index, actual.bone_index)


def get_hlod_array():
    array = HLodArray(
        header=get_hlod_array_header(),
        sub_objects=[])

    array.sub_objects = [
                        get_hlod_sub_object(bone=0, name="containerName.sword"),
                        get_hlod_sub_object(bone=0, name="containerName.soldier"),
                        get_hlod_sub_object(bone=6, name="containerName.TRUNK"),
                        get_hlod_sub_object(bone=0, name="containerName.PICK"),
                        get_hlod_sub_object(bone=0, name="containerName.BOUNDINGBOX")]

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
        lod_arrays=[get_hlod_array()])


def get_hlod_minimal(model_name="containerName", hierarchy_name="TestHierarchy"):
    return HLod(
        header=get_hlod_header(model_name, hierarchy_name),
        lod_arrays=[get_hlod_array_minimal()])


def get_hlod_4_levels(model_name="containerName", hierarchy_name="TestHierarchy"):
    array0 = HLodArray(
        header=get_hlod_array_header(count=3, size=0.0),
        sub_objects=[])

    array0.sub_objects = [get_hlod_sub_object(bone=1, name="containerName.mesh1"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh2"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh3")]

    array1 = HLodArray(
        header=get_hlod_array_header(count=3, size=1.0),
        sub_objects=[])

    array1.sub_objects = [get_hlod_sub_object(bone=1, name="containerName.mesh1_1"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh2_1"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh3_1")]

    array2 = HLodArray(
        header=get_hlod_array_header(count=3, size=0.3),
        sub_objects=[])

    array2.sub_objects = [get_hlod_sub_object(bone=1, name="containerName.mesh1_2"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh2_2"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh3_2")]

    array3 = HLodArray(
        header=get_hlod_array_header(count=3, size=0.03),
        sub_objects=[])

    array3.sub_objects = [get_hlod_sub_object(bone=1, name="containerName.mesh1_3"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh2_3"),
                            get_hlod_sub_object(bone=1, name="containerName.mesh3_3")]

    return HLod(
        header=get_hlod_header(model_name, hierarchy_name, lod_count=4),
        lod_arrays=[array3, array2, array1, array0])


def compare_hlods(self, expected, actual):
    compare_hlod_headers(self, expected.header, actual.header)
    self.assertEqual(len(expected.lod_arrays), len(actual.lod_arrays))

    for i, expected_array in enumerate(expected.lod_arrays):
        compare_hlod_arrays(self, expected_array, actual.lod_arrays[i])
