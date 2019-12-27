# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from io_mesh_w3d.structs.w3d_animation import *
from tests.helpers.w3d_version import *
from tests.utils import almost_equal


def get_animation_header(hierarchy_name="hierarchy"):
    return AnimationHeader(
        version=get_version(),
        name="containerName",
        hierarchy_name=hierarchy_name,
        num_frames=5,
        frame_rate=30)


def compare_animation_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.hierarchy_name, actual.hierarchy_name)
    self.assertEqual(expected.num_frames, actual.num_frames)
    self.assertEqual(expected.frame_rate, actual.frame_rate)


def get_animation_channel(type=1, pivot=0):
    channel = AnimationChannel(
        first_frame=0,
        last_frame=4,
        type=type,
        pivot=pivot,
        unknown=0,
        data=[])

    if type == 6:
        channel.vector_len = 4

        channel.data.append(Quaternion((-.1, -2.1, -1.7, -1.7)))
        channel.data.append(Quaternion((-0.1, -2.1, 1.6, 1.6)))
        channel.data.append(Quaternion((0.9, -2.1, 1.6, 1.6)))
        channel.data.append(Quaternion((0.9, 1.8, 1.6, 1.6)))
        channel.data.append(Quaternion((0.9, 1.8, -1.6, 1.6)))
    else:
        channel.vector_len = 1

        channel.data.append(3.0)
        channel.data.append(3.5)
        channel.data.append(2.0)
        channel.data.append(1.0)
        channel.data.append(-1.0)
    return channel


def compare_animation_channels(self, expected, actual):
    self.assertEqual(expected.first_frame, actual.first_frame)
    self.assertEqual(expected.last_frame, actual.last_frame)
    self.assertEqual(expected.vector_len, actual.vector_len)
    self.assertEqual(expected.type, actual.type)
    self.assertEqual(expected.pivot, actual.pivot)
    self.assertEqual(expected.unknown, actual.unknown)

    self.assertEqual(len(expected.data), len(actual.data))
    for i in range(len(expected.data)):
        if expected.type < 6:
            self.assertAlmostEqual(expected.data[i], actual.data[i], 5)
        else:
            almost_equal(self, expected.data[i][0], actual.data[i][0], 0.2)
            almost_equal(self, expected.data[i][1], actual.data[i][1], 0.2)
            almost_equal(self, expected.data[i][2], actual.data[i][2], 0.2)
            almost_equal(self, expected.data[i][3], actual.data[i][3], 0.2)


def get_animation_bit_channel(pivot=0):
    channel = AnimationBitChannel(
        first_frame=0,
        last_frame=9,
        type=0,
        pivot=pivot,
        default=False,
        data=[])

    channel.data.append(True)
    channel.data.append(True)
    channel.data.append(True)
    channel.data.append(True)
    channel.data.append(True)
    channel.data.append(True)
    channel.data.append(True)
    channel.data.append(False)
    channel.data.append(False)
    channel.data.append(False)
    return channel


def compare_animation_bit_channels(self, expected, actual):
    self.assertEqual(expected.first_frame, actual.first_frame)
    self.assertEqual(expected.last_frame, actual.last_frame)
    self.assertEqual(expected.type, actual.type)
    self.assertEqual(expected.pivot, actual.pivot)
    self.assertEqual(expected.default, actual.default)

    self.assertEqual(len(expected.data), len(actual.data))
    for i, datum in enumerate(expected.data):
        self.assertEqual(datum, actual.data[i])


def get_animation(hierarchy_name="TestHierarchy"):
    animation = Animation(
        header=get_animation_header(hierarchy_name),
        channels=[])

    animation.channels.append(get_animation_channel(type=0, pivot=1))
    animation.channels.append(get_animation_channel(type=1, pivot=1))
    animation.channels.append(get_animation_channel(type=2, pivot=1))

    animation.channels.append(get_animation_channel(type=0, pivot=2))
    animation.channels.append(get_animation_channel(type=1, pivot=2))
    animation.channels.append(get_animation_channel(type=2, pivot=2))
    animation.channels.append(get_animation_channel(type=6, pivot=2))

    animation.channels.append(get_animation_channel(type=0, pivot=3))
    animation.channels.append(get_animation_channel(type=1, pivot=3))
    animation.channels.append(get_animation_channel(type=2, pivot=3))
    animation.channels.append(get_animation_channel(type=6, pivot=3))

    animation.channels.append(get_animation_bit_channel(pivot=5))
    animation.channels.append(get_animation_bit_channel(pivot=7))
    return animation


def get_animation_minimal():
    return Animation(
        header=get_animation_header(),
        channels=[get_animation_channel()])


def get_animation_empty():
    return Animation(
        header=get_animation_header(),
        channels=[])


def compare_animations(self, expected, actual):
    compare_animation_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.channels), len(actual.channels))
    for i, chan in enumerate(expected.channels):
        if isinstance(chan, AnimationBitChannel):
            continue
        match_found = False
        for act in actual.channels:
            if isinstance(act, AnimationBitChannel):
                continue
            
            if chan.type == act.type and chan.pivot == act.pivot:
                compare_animation_channels(self, chan, act)
                match_found = True
        self.assertTrue(match_found)

    for i, chan in enumerate(expected.channels):
        if isinstance(chan, AnimationChannel):
            continue
        match_found = False
        for act in actual.channels:
            if isinstance(act, AnimationChannel):
                continue

            if chan.type == act.type and chan.pivot == act.pivot:
                compare_animation_bit_channels(self, chan, act)
                match_found = True
        self.assertTrue(match_found)
