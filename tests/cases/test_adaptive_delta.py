# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d_adaptive_delta import *
from tests import utils
from tests.helpers.w3d_compressed_animation import *
from tests.helpers.w3d_animation import *


class TestAdaptiveDelta(utils.W3dTestCase):
    def test_get_deltas_4bit(self):
        deltaBytes = [-3, 17, -32, -101, 120, 88, -20, -1]
        deltas = get_deltas(deltaBytes, 4)
        expected = [-3, -1, 1, 1, 0, -2, -5, -
                    7, -8, 7, -8, 5, -4, -2, -1, -1]
        self.assertEqual(expected, deltas)

    def test_get_deltas_8bit(self):
        deltaBytes = [-49, -50, -53, -57, -62, -69, -
                      73, -75, -82, -94, -111, 123, 82, 37, 12, 4]
        deltas = get_deltas(deltaBytes, 8)
        expected = [79, 78, 75, 71, 66, 59, 55, 53,
                    46, 34, 17, -5, -46, -91, -116, -124]
        self.assertEqual(expected, deltas)

    def test_set_deltas_4bit(self):
        bytes = [-3, -1, 1, 1, 0, -2, -5, -
                    7, -8, 7, -8, 5, -4, -2, -1, -1]
        expected = [-3, 17, -32, -101, 120, 88, -20, -1]
        actual = set_deltas(bytes, 4)

        self.assertEqual(expected, actual)

    def test_set_deltas_8bit(self):
        bytes = [79, 78, 75, 71, 66, 59, 55, 53,
                    46, 34, 17, -5, -46, -91, -116, -124]
        expected = [-49, -50, -53, -57, -62, -69, -
                      73, -75, -82, -94, -111, 123, 82, 37, 12, 4]
        actual = set_deltas(bytes, 8)

        self.assertEqual(expected, actual)

    def test_decode(self):
        channel = get_motion_channel(type=0, delta_type=1, num_time_codes=5)
        expected = [-3.14, -3.14, -3.14,  -3.136, -3.136]

        actual = decode(channel)

        self.assertEqual(len(expected), len(actual))
        self.assertEqual(expected, actual)

    def test_encode_4bit(self):
        channel = AnimationChannel(
            first_frame=0,
            last_frame=7,
            type=1,
            pivot=2,
            unknown=0,
            data=[0, 1, 2, 3, 4, 5, 6, 7])
        expected = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]

        actual = encode(channel, num_bits=4)

        #self.assertEqual(len(expected), len(actual))