# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from mathutils import Quaternion

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_animation import Animation, AnimationHeader, AnimationChannel

def get_animation_header():
    return AnimationHeader(
        version=Version(major=4, minor=1),
        name="AniHeader",
        hierarchy_name="HieraName",
        num_frames=155,
        frame_rate=300)

def compare_animation_headers(self, expected, actual):
    self.assertEqual(expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.hierarchy_name, actual.hierarchy_name)
    self.assertEqual(expected.num_frames, actual.num_frames)
    self.assertEqual(expected.frame_rate, actual.frame_rate)

def get_animation_channel(_type):
    channel = AnimationChannel(
        first_frame=1,
        last_frame=33,
        type=_type,
        pivot=33,
        unknown=123,
        data=[])

    if _type == 6:
        channel.vector_len = 4
    else:
        channel.vector_len = 1

    for i in range(channel.first_frame, channel.last_frame):
        if _type == 6:
            channel.data.append(Quaternion((1.0, 0.0, 0.9, 0.0)))
        else:
            channel.data.append(1.0 * i)
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
        self.assertAlmostEqual(expected.data[i], actual.data[i], 5)

def get_animation():
    animation = Animation(
        header=get_animation_header(),
        channels=[])

    animation.channels.append(get_animation_channel(0))
    animation.channels.append(get_animation_channel(1))
    animation.channels.append(get_animation_channel(2))
    animation.channels.append(get_animation_channel(6))
    return animation

def compare_animations(self, expected, actual):
    compare_animation_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.channels), len(actual.channels))
    for i in range(len(expected.channels)):
        compare_animation_channels(self, expected.channels[i], actual.channels[i])
