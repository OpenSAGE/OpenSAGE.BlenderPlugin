# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
import bpy
from io_mesh_w3d.common.structs.animation import *
from tests.mathutils import *
from tests.w3d.helpers.version import *


def get_animation_header(hierarchy_name='hierarchy'):
    return AnimationHeader(
        version=get_version(major=4, minor=1),
        name='containerName',
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
        unknown=0)

    channel.pad_bytes = [0xff, 0xff, 0xff]

    if type == 6:
        channel.vector_len = 4
        channel.data = [get_quat(-.842, -0.002, -0.512, 0.171),
                        get_quat(1, 0, 0, 0),
                        get_quat(0.75, 0.433, 0.433, 0.250),
                        get_quat(0.525, 0.592, 0.158, 0.592),
                        get_quat(0.158, 0.592, 0.525, 0.592)]
    else:
        channel.vector_len = 1
        channel.data = [3.0, 3.5, 2.0, 1.0, -1.0]
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
            compare_quats(self, expected.data[i], actual.data[i])


def get_animation_bit_channel(pivot=0, xml=False):
    data = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    if xml:
        data = [0.0, 1.0, 1.0, 1.0, 0.0, 0.57, 0.33, 1.0, 1.0, 1.0]
    return AnimationBitChannel(
        first_frame=0,
        last_frame=len(data) - 1,
        type=0,
        pivot=pivot,
        default=1.0,
        data=data)


def get_animation_bit_channel_no_pad(pivot=0):
    return AnimationBitChannel(
        first_frame=0,
        last_frame=7,
        type=0,
        pivot=pivot,
        default=0.0,
        data=[1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 0.0])


def compare_animation_bit_channels(self, expected, actual):
    self.assertEqual(expected.first_frame, actual.first_frame)
    self.assertEqual(expected.last_frame, actual.last_frame)
    self.assertEqual(expected.type, actual.type)
    self.assertEqual(expected.pivot, actual.pivot)
    self.assertEqual(expected.default, actual.default)

    self.assertEqual(len(expected.data), len(actual.data))
    for i, datum in enumerate(expected.data):
        self.assertAlmostEqual(datum, actual.data[i], 4)


def get_animation(hierarchy_name='TestHierarchy', xml=False):
    channels = [
                  get_animation_channel(type=0, pivot=0),
                  get_animation_channel(type=1, pivot=1),
                  get_animation_channel(type=2, pivot=1),

                  get_animation_channel(type=0, pivot=2),
                  get_animation_channel(type=1, pivot=2),
                  get_animation_channel(type=2, pivot=2),
                  get_animation_channel(type=6, pivot=2),

                  get_animation_channel(type=0, pivot=3),
                  get_animation_channel(type=1, pivot=3),
                  get_animation_channel(type=2, pivot=3),
                  get_animation_channel(type=6, pivot=3),
                ]
    
    if bpy.app.version != (4, 4, 3): #TODO fix 4.4.3
        channels.append(get_animation_bit_channel(pivot=6, xml=xml))
        channels.append(get_animation_bit_channel(pivot=7))
    
    return Animation(
        header=get_animation_header(hierarchy_name),
        channels=channels)


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
