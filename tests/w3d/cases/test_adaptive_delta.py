# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest

from io_mesh_w3d.w3d.adaptive_delta import *
from tests.common.helpers.animation import *
from tests.w3d.helpers.compressed_animation import *
from tests.utils import TestCase


class TestAdaptiveDelta(TestCase):
    def test_get_deltas_4bit(self):
        delta_bytes = [-3, 17, -32, -101, 120, 88, -20, -1]
        deltas = get_deltas(delta_bytes, 4)
        expected = [-3, -1, 1, 1, 0, -2, -5, -7, -8, 7, -8, 5, -4, -2, -1, -1]
        self.assertEqual(expected, deltas)

    def test_get_deltas_8bit(self):
        delta_bytes = [-49, -50, -53, -57, -62, -69, -73, -75, -82, -94, -111, 123, 82, 37, 12, 4]
        deltas = get_deltas(delta_bytes, 8)
        expected = [79, 78, 75, 71, 66, 59, 55, 53, 46, 34, 17, -5, -46, -91, -116, -124]
        self.assertEqual(expected, deltas)

    def test_set_deltas_4bit(self):
        delta_bytes = [-3, -1, 1, 1, 0, -2, -5, -7, -8, 7, -8, 5, -4, -2, -1, -1]
        expected = [-3, 17, -32, -101, 120, 88, -20, -1]
        actual = set_deltas(delta_bytes, 4)

        self.assertEqual(expected, actual)

    def test_set_deltas_8bit(self):
        delta_bytes = [79, 78, 75, 71, 66, 59, 55, 53, 46, 34, 17, -5, -46, -91, -116, -124]
        expected = [-49, -50, -53, -57, -62, -69, -73, -75, -82, -94, -111, 123, 82, 37, 12, 4]
        actual = set_deltas(delta_bytes, 8)

        self.assertEqual(expected, actual)

    def test_decode(self):
        channel = get_motion_channel(channel_type=0, delta_type=1, num_time_codes=5)
        expected = [4.3611, 4.6254, 4.9559, 5.4186, 5.8812]

        actual = decode(channel)

        self.assertEqual(len(expected), len(actual))
        for i, value in enumerate(expected):
            self.assertAlmostEqual(value, actual[i], 3)

    def test_encode_8bit(self):
        channel = AnimationChannel(
            first_frame=0,
            last_frame=7,
            channel_type=1,
            pivot=2,
            unknown=0,
            data=[4.3611, 4.3611, 4.6254, 4.9559, 5.4186, 5.8812])
        expected = [95, 44, 12, 2, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        actual = encode(channel, num_bits=8)

        # self.assertEqual(len(expected), len(actual))
        # self.assertEqual(expected, actual)

    def test_encode_4bit(self):
        channel = AnimationChannel(
            first_frame=0,
            last_frame=7,
            channel_type=1,
            pivot=2,
            unknown=0,
            data=[4.3611, 4.3611, 4.6254, 4.9559, 5.4186, 5.8812])
        expected = []  # ?

        actual = encode(channel, num_bits=4)

        # self.assertEqual(len(expected), len(actual))
        # self.assertEqual(expected, actual)
