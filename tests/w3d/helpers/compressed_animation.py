# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from random import random

from io_mesh_w3d.w3d.structs.compressed_animation import *
from tests.mathutils import *
from tests.w3d.helpers.version import get_version, compare_versions


def get_compressed_animation_header(
        hierarchy_name='hierarchy', flavor=ADAPTIVE_DELTA_FLAVOR):
    return CompressedAnimationHeader(
        version=get_version(major=0, minor=1),
        name='containerName',
        hierarchy_name=hierarchy_name,
        num_frames=155,
        frame_rate=300,
        flavor=flavor)


def compare_compressed_animation_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.hierarchy_name, actual.hierarchy_name)
    self.assertEqual(expected.num_frames, actual.num_frames)
    self.assertEqual(expected.frame_rate, actual.frame_rate)
    self.assertEqual(expected.flavor, actual.flavor)


def get_time_coded_datum(time_code, datum_type=0, random_interpolation=True):
    datum = TimeCodedDatum(
        time_code=time_code,
        interpolated=True)

    if random_interpolation:
        datum.interpolated = (random() >= 0.5)

    if datum_type == 6:
        datum.value = get_quat(0.1, -2.0, -0.3, 2.0)
    else:
        datum.value = 3.14
    return datum


def compare_time_coded_datums(self, datum_type, expected, actual):
    self.assertEqual(expected.time_code, actual.time_code)
    self.assertEqual(expected.interpolated, actual.interpolated)

    if datum_type == 6:
        compare_quats(self, expected.value, actual.value)
    else:
        self.assertAlmostEqual(expected.value, actual.value, 2)


def get_time_coded_animation_channel(channel_type=0, random_interpolation=True):
    channel = TimeCodedAnimationChannel(
        num_time_codes=5,
        pivot=4,
        channel_type=channel_type,
        time_codes=[])

    values = []
    if channel_type == 6:
        channel.vector_len = 4
        values = [get_quat(-0.6, -0.4, 0.3, -0.8),
                  get_quat(0.6, 1.2, 0.3, -0.8),
                  get_quat(-0.6, 1.2, -0.7, -2.1),
                  get_quat(-1.7, 0.0, 0.3, -2.1),
                  get_quat(-1.7, 1.2, -0.7, 0.0)]
    else:
        channel.vector_len = 1
        values = [3.0, 3.5, 2.0, 1.0, -1.0]

    for i, value in enumerate(values):
        datum = TimeCodedDatum(
            time_code=i,
            value=value)
        if random_interpolation:
            datum.interpolated = (random() < 0.5)
        channel.time_codes.append(datum)
    return channel


def get_time_coded_animation_channel_minimal():
    return TimeCodedAnimationChannel(
        num_time_codes=55,
        pivot=4,
        channel_type=1,
        time_codes=[get_time_coded_datum(0)])


def get_time_coded_animation_channel_empty():
    return TimeCodedAnimationChannel(
        num_time_codes=55,
        pivot=4,
        channel_type=1,
        time_codes=[])


def compare_time_coded_animation_channels(self, expected, actual):
    self.assertEqual(expected.num_time_codes, actual.num_time_codes)
    self.assertEqual(expected.pivot, actual.pivot)
    self.assertEqual(expected.vector_len, actual.vector_len)
    self.assertEqual(expected.channel_type, actual.channel_type)

    self.assertEqual(len(expected.time_codes), len(actual.time_codes))
    for i in range(len(expected.time_codes)):
        compare_time_coded_datums(self, expected.channel_type, expected.time_codes[i], actual.time_codes[i])


def get_time_coded_bit_datum():
    return TimeCodedBitDatum(
        time_code=1,
        value=random() < 0.5)


def compare_time_coded_bit_datas(self, expected, actual):
    self.assertEqual(expected.time_code, actual.time_code)
    self.assertEqual(expected.value, actual.value)


def get_time_coded_bit_channel():
    channel = TimeCodedBitChannel(
        num_time_codes=55,
        pivot=1,
        channel_type=0,
        default_value=12,
        time_codes=[])

    for _ in range(channel.num_time_codes):
        channel.time_codes.append(get_time_coded_bit_datum())
    return channel


def get_time_coded_bit_channel_minimal():
    return TimeCodedBitChannel(
        num_time_codes=55,
        pivot=1,
        channel_type=0,
        default_value=12,
        time_codes=[get_time_coded_bit_datum()])


def get_time_coded_bit_channel_empty():
    return TimeCodedBitChannel(
        num_time_codes=55,
        pivot=1,
        channel_type=0,
        default_value=12,
        time_codes=[])


def compare_time_coded_bit_channels(self, expected, actual):
    self.assertEqual(expected.num_time_codes, actual.num_time_codes)
    self.assertEqual(expected.pivot, actual.pivot)
    self.assertEqual(expected.channel_type, actual.channel_type)
    self.assertAlmostEqual(expected.default_value, actual.default_value, 5)

    self.assertEqual(len(expected.time_codes), len(actual.time_codes))
    for i in range(len(expected.time_codes)):
        compare_time_coded_bit_datas(self, expected.time_codes[i], actual.time_codes[i])


def get_adaptive_delta_block(data, delta_type, index):
    ad_block = AdaptiveDeltaBlock(
        vector_index=0,
        block_index=33,
        delta_bytes=data)
    if delta_type == 6:
        ad_block.vector_index = index
    return ad_block


def compare_adaptive_delta_blocks(self, expected, actual):
    self.assertEqual(expected.vector_index, actual.vector_index)
    self.assertEqual(expected.block_index, actual.block_index)
    self.assertEqual(len(expected.delta_bytes), len(actual.delta_bytes))
    for i in range(len(expected.delta_bytes)):
        self.assertEqual(expected.delta_bytes[i], actual.delta_bytes[i])


def get_adaptive_delta_data(delta_type, num_bits, num_time_codes=33):
    data = [84, 119, 119, 53, 0, 16, 82, 0]
    if num_bits == 8:
        data = [95, 44, 12, 2, 12, 44, 96, -99, -
                53, -25, -17, -25, -53, -99, -128, -128]

    ad_data = AdaptiveDeltaData(
        bit_count=num_bits,
        delta_blocks=[])

    if delta_type == 6:
        vec_len = 4
        ad_data.initial_value = get_quat(0.9904, 0.1199, -0.0631, 0.0284)
    else:
        vec_len = 1
        ad_data.initial_value = 4.3611

    count = int(num_time_codes / 16) + 1
    for _ in range(count):
        for i in range(vec_len):
            ad_data.delta_blocks.append(get_adaptive_delta_block(data, delta_type, i))
    return ad_data


def compare_adaptive_delta_datas(self, expected, actual, delta_type):
    self.assertEqual(expected.size(delta_type), actual.size(delta_type))
    self.assertEqual(expected.bit_count, actual.bit_count)
    self.assertEqual(len(expected.delta_blocks), len(actual.delta_blocks))
    if delta_type == 6:
        compare_quats(self, expected.initial_value, actual.initial_value)
    else:
        self.assertAlmostEqual(expected.initial_value, actual.initial_value, 2)
    for i in range(len(expected.delta_blocks)):
        compare_adaptive_delta_blocks(self, expected.delta_blocks[i], actual.delta_blocks[i])


def get_adaptive_delta_animation_channel(channel_type, num_bits=4):
    channel = AdaptiveDeltaAnimationChannel(
        pivot=3,
        channel_type=channel_type,
        scale=2,
        num_time_codes=5,
        data=None)

    if channel_type == 6:
        channel.vector_len = 4
    else:
        channel.vector_len = 1

    channel.data = get_adaptive_delta_data(channel_type, num_bits, channel.num_time_codes)
    return channel


def get_adaptive_delta_animation_channel_minimal():
    return AdaptiveDeltaAnimationChannel(
        pivot=3,
        channel_type=2,
        scale=4,
        vector_len=1,
        num_time_codes=5,
        data=get_adaptive_delta_data(2, 4, 5))


def compare_adaptive_delta_animation_channels(self, expected, actual):
    self.assertEqual(expected.pivot, actual.pivot)
    self.assertEqual(expected.vector_len, actual.vector_len)
    self.assertEqual(expected.channel_type, actual.channel_type)
    self.assertEqual(expected.scale, actual.scale)
    self.assertEqual(expected.num_time_codes, actual.num_time_codes)
    compare_adaptive_delta_datas(self, expected.data, actual.data, expected.channel_type)


def get_adaptive_delta_motion_animation_channel(channel_type, num_bits, num_time_codes):
    return AdaptiveDeltaMotionAnimationChannel(
        scale=0.07435,
        data=get_adaptive_delta_data(channel_type, num_bits, num_time_codes))


def compare_adaptive_delta_motion_animation_channels(self, expected, actual, channel_type):
    self.assertAlmostEqual(expected.scale, actual.scale, 5)
    compare_adaptive_delta_datas(self, expected.data, actual.data, channel_type)


def get_motion_channel(channel_type, delta_type, num_time_codes=55):
    channel = MotionChannel(
        delta_type=delta_type,
        channel_type=channel_type,
        num_time_codes=num_time_codes,
        pivot=3,
        data=[])

    if channel_type == 6:
        channel.vector_len = 4
    else:
        channel.vector_len = 1

    if delta_type == 0:
        for _ in range(channel.num_time_codes):
            channel.data.append(get_time_coded_datum(0, channel_type, False))
    elif delta_type == 1:
        channel.data = get_adaptive_delta_motion_animation_channel(
            channel_type, 4, channel.num_time_codes)
    elif delta_type == 2:
        channel.data = get_adaptive_delta_motion_animation_channel(
            channel_type, 8, channel.num_time_codes)
    return channel


def get_motion_channel_minimal():
    return MotionChannel(
        delta_type=0,
        channel_type=2,
        num_time_codes=1,
        pivot=3,
        data=[get_time_coded_datum(0, 2, False)])


def get_motion_channel_empty():
    return MotionChannel(
        delta_type=0,
        channel_type=2,
        num_time_codes=1,
        pivot=3,
        data=[])


def compare_motion_channels(self, expected, actual):
    self.assertEqual(expected.delta_type, actual.delta_type)
    self.assertEqual(expected.channel_type, actual.channel_type)
    self.assertEqual(expected.num_time_codes, actual.num_time_codes)
    self.assertEqual(expected.pivot, actual.pivot)

    if expected.delta_type == 0:
        self.assertEqual(len(expected.data), len(actual.data))
        for i in range(len(expected.data)):
            compare_time_coded_datums(self, expected.channel_type, expected.data[i], actual.data[i])
    else:
        compare_adaptive_delta_motion_animation_channels(
            self, expected.data, actual.data, expected.channel_type)


def get_compressed_animation(
        hierarchy_name='TestHierarchy',
        flavor=TIME_CODED_FLAVOR,
        bit_channels=True,
        motion_tc=True,
        motion_ad4=True,
        motion_ad8=True,
        random_interpolation=True):
    animation = CompressedAnimation(
        header=get_compressed_animation_header(hierarchy_name, flavor),
        time_coded_channels=[],
        adaptive_delta_channels=[],
        time_coded_bit_channels=[],
        motion_channels=[])

    if flavor == TIME_CODED_FLAVOR:
        animation.time_coded_channels.append(
            get_time_coded_animation_channel(channel_type=0, random_interpolation=random_interpolation))
        animation.time_coded_channels.append(
            get_time_coded_animation_channel(channel_type=1, random_interpolation=random_interpolation))
        animation.time_coded_channels.append(
            get_time_coded_animation_channel(channel_type=2, random_interpolation=random_interpolation))
        animation.time_coded_channels.append(
            get_time_coded_animation_channel(channel_type=6, random_interpolation=random_interpolation))

    else:
        animation.adaptive_delta_channels.append(
            get_adaptive_delta_animation_channel(channel_type=0, num_bits=4))
        animation.adaptive_delta_channels.append(
            get_adaptive_delta_animation_channel(channel_type=1, num_bits=4))
        animation.adaptive_delta_channels.append(
            get_adaptive_delta_animation_channel(channel_type=2, num_bits=4))
        animation.adaptive_delta_channels.append(
            get_adaptive_delta_animation_channel(channel_type=6, num_bits=4))

    if bit_channels:
        animation.time_coded_bit_channels.append(get_time_coded_bit_channel())
        animation.time_coded_bit_channels.append(get_time_coded_bit_channel())

    if motion_tc:
        animation.motion_channels.append(get_motion_channel(channel_type=0, delta_type=0, num_time_codes=50))
        animation.motion_channels.append(get_motion_channel(channel_type=1, delta_type=0, num_time_codes=50))
        animation.motion_channels.append(get_motion_channel(channel_type=2, delta_type=0))
        animation.motion_channels.append(get_motion_channel(channel_type=6, delta_type=0))

    if motion_ad4:
        animation.motion_channels.append(get_motion_channel(channel_type=0, delta_type=1))
        animation.motion_channels.append(get_motion_channel(channel_type=1, delta_type=1))
        animation.motion_channels.append(get_motion_channel(channel_type=2, delta_type=1))
        animation.motion_channels.append(get_motion_channel(channel_type=6, delta_type=1))

    if motion_ad8:
        animation.motion_channels.append(get_motion_channel(channel_type=0, delta_type=2))
        animation.motion_channels.append(get_motion_channel(channel_type=1, delta_type=2))
        animation.motion_channels.append(get_motion_channel(channel_type=2, delta_type=2))
        animation.motion_channels.append(get_motion_channel(channel_type=6, delta_type=2))

    return animation


def get_compressed_animation_minimal(hierarchy_name='TestHierarchy'):
    return CompressedAnimation(
        header=get_compressed_animation_header(hierarchy_name),
        time_coded_channels=[get_time_coded_animation_channel_minimal()],
        adaptive_delta_channels=[get_adaptive_delta_animation_channel_minimal()],
        time_coded_bit_channels=[get_time_coded_bit_channel_minimal()],
        motion_channels=[get_motion_channel_minimal()])


def get_compressed_animation_empty(hierarchy_name='TestHierarchy'):
    return CompressedAnimation(
        header=get_compressed_animation_header(hierarchy_name),
        time_coded_channels=[],
        adaptive_delta_channels=[],
        time_coded_bit_channels=[],
        motion_channels=[])


def compare_compressed_animations(self, expected, actual):
    compare_compressed_animation_headers(self, expected.header, actual.header)
    self.assertEqual(len(expected.time_coded_channels), len(actual.time_coded_channels))
    for i in range(len(expected.time_coded_channels)):
        compare_time_coded_animation_channels(
            self, expected.time_coded_channels[i], actual.time_coded_channels[i])
    self.assertEqual(len(expected.adaptive_delta_channels), len(actual.adaptive_delta_channels))
    for i in range(len(expected.adaptive_delta_channels)):
        compare_adaptive_delta_animation_channels(
            self, expected.adaptive_delta_channels[i], actual.adaptive_delta_channels[i])
    self.assertEqual(len(expected.time_coded_bit_channels), len(actual.time_coded_bit_channels))
    for i in range(len(expected.time_coded_bit_channels)):
        compare_time_coded_bit_channels(self,
                                        expected.time_coded_bit_channels[i],
                                        actual.time_coded_bit_channels[i])
    self.assertEqual(len(expected.motion_channels), len(actual.motion_channels))
    for i in range(len(expected.motion_channels)):
        compare_motion_channels(self, expected.motion_channels[i], actual.motion_channels[i])
