# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.hlod import *
from tests.w3d.helpers.version import get_version, compare_versions


def get_hlod_header(model_name, hierarchy_name, lod_count=1):
    return HLodHeader(
        version=get_version(major=1, minor=0),
        lod_count=lod_count,
        model_name=model_name,
        hierarchy_name=hierarchy_name)


def compare_hlod_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.lod_count, actual.lod_count)
    self.assertEqual(expected.model_name, actual.model_name)
    self.assertEqual(expected.hierarchy_name, actual.hierarchy_name)


def get_hlod_array_header(count=0, size=MAX_SCREEN_SIZE):
    return HLodArrayHeader(
        model_count=count,
        max_screen_size=size)


def compare_hlod_array_headers(self, expected, actual):
    self.assertEqual(expected.model_count, actual.model_count)
    self.assertAlmostEqual(expected.max_screen_size, actual.max_screen_size, 2)


def get_hlod_sub_object(bone=0, name='containerName.default'):
    return HLodSubObject(
        bone_index=bone,
        identifier=name,
        name=name.split('.', 1)[-1])


def compare_hlod_sub_objects(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.identifier, actual.identifier)
    self.assertEqual(expected.bone_index, actual.bone_index)


def get_hlod_array(array):
    array.header = get_hlod_array_header()

    array.sub_objects = [
        get_hlod_sub_object(bone=0, name='containerName.sword'),
        get_hlod_sub_object(bone=0, name='containerName.soldier'),
        get_hlod_sub_object(bone=6, name='containerName.TRUNK'),
        get_hlod_sub_object(bone=0, name='containerName.PICK'),
        get_hlod_sub_object(bone=0, name='containerName.BOUNDINGBOX'),
        get_hlod_sub_object(bone=1, name='containerName.Brakelight')]

    array.header.model_count = len(array.sub_objects)
    return array


def get_hlod_lod_array():
    return get_hlod_array(HLodLodArray())


def get_hlod_aggregate_array():
    return get_hlod_array(HLodAggregateArray())


def get_hlod_proxy_array():
    return get_hlod_array(HLodProxyArray())


def get_hlod_array_minimal(array):
    array.header = get_hlod_array_header()
    array.sub_objects = [get_hlod_sub_object(
        bone=0, name='containerName.BOUNDINGBOX')]
    array.header.model_count = len(array.sub_objects)
    return array


def get_hlod_lod_array_minimal():
    return get_hlod_array_minimal(HLodLodArray())


def get_hlod_aggregate_array_minimal():
    return get_hlod_array_minimal(HLodAggregateArray())


def get_hlod_proxy_array_minimal():
    return get_hlod_array_minimal(HLodProxyArray())


def compare_hlod_arrays(self, expected, actual, xml=False):
    if not xml:
        compare_hlod_array_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.sub_objects), len(actual.sub_objects))
    for i in range(len(expected.sub_objects)):
        compare_hlod_sub_objects(
            self, expected.sub_objects[i], actual.sub_objects[i])


def get_hlod(model_name='containerName', hierarchy_name='TestHierarchy'):
    return HLod(
        header=get_hlod_header(model_name, hierarchy_name),
        lod_arrays=[get_hlod_lod_array()],
        aggregate_array=get_hlod_aggregate_array(),
        proxy_array=get_hlod_proxy_array())


def get_hlod_minimal(model_name='containerName', hierarchy_name='TestHierarchy'):
    return HLod(
        header=get_hlod_header(model_name, hierarchy_name),
        lod_arrays=[get_hlod_lod_array_minimal()],
        aggregate_array=get_hlod_aggregate_array_minimal(),
        proxy_array=get_hlod_proxy_array_minimal())


def get_hlod_4_levels(model_name='containerName', hierarchy_name='TestHierarchy'):
    array0 = HLodLodArray(
        header=get_hlod_array_header(count=3, size=MAX_SCREEN_SIZE),
        sub_objects=[])

    array0.sub_objects = [get_hlod_sub_object(bone=1, name='containerName.mesh1'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh2'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh3')]

    array1 = HLodLodArray(
        header=get_hlod_array_header(count=3, size=1.0),
        sub_objects=[])

    array1.sub_objects = [get_hlod_sub_object(bone=1, name='containerName.mesh1_1'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh2_1'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh3_1')]

    array2 = HLodLodArray(
        header=get_hlod_array_header(count=3, size=0.3),
        sub_objects=[])

    array2.sub_objects = [get_hlod_sub_object(bone=1, name='containerName.mesh1_2'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh2_2'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh3_2')]

    array3 = HLodLodArray(
        header=get_hlod_array_header(count=3, size=0.03),
        sub_objects=[])

    array3.sub_objects = [get_hlod_sub_object(bone=1, name='containerName.mesh1_3'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh2_3'),
                          get_hlod_sub_object(bone=1, name='containerName.mesh3_3')]

    return HLod(
        header=get_hlod_header(model_name, hierarchy_name, lod_count=4),
        lod_arrays=[array3, array2, array1, array0])


def compare_hlods(self, expected, actual, xml=False):
    if not xml:
        compare_hlod_headers(self, expected.header, actual.header)
        self.assertEqual(len(expected.lod_arrays), len(actual.lod_arrays))

    for i, expected_array in enumerate(expected.lod_arrays):
        compare_hlod_arrays(self, expected_array, actual.lod_arrays[i], xml)

    # roundtrip not supported
    if expected.aggregate_array is not None and actual.aggregate_array is not None:
        compare_hlod_arrays(self, expected.aggregate_array, actual.aggregate_array)

    # roundtrip not supported
    if actual.proxy_array is not None and actual.proxy_array is not None:
        compare_hlod_arrays(self, expected.proxy_array, actual.proxy_array)
