# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Quaternion

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_compressed_animation import CompressedAnimation, CompressedAnimationHeader, \
    MotionChannel, TimeCodedBitChannel, AdaptiveDeltaData, AdaptiveDeltaBlock, AdaptiveDeltaMotionAnimationChannel, \
    AdaptiveDeltaAnimationChannel, TimeCodedAnimationChannel, TimeCodedBitDatum, TimeCodedDatum, \
    W3D_CHUNK_COMPRESSED_ANIMATION
from io_mesh_w3d.io_binary import read_chunk_head


class TestCompressedAnimation(unittest.TestCase):
    def test_write_read(self):
        expected = CompressedAnimation(
            time_coded_channels=[],
            adaptive_delta_channels=[],
            time_coded_bit_channels=[],
            motion_channels=[])

        expected.header = CompressedAnimationHeader(
            version=Version(major=4, minor=1),
            name="CompAniHead",
            hierarchy_name="HieraName",
            num_frames=155,
            frame_rate=300,
            flavor=0)

        self.assertEqual(44, expected.header.size_in_bytes())

        tc_channel = TimeCodedAnimationChannel(
            pivot=4,
            vector_len=4,
            type=6,
            time_codes=[])

        tc_datum = TimeCodedDatum(
            time_code=34,
            non_interpolated=True,
            value=Quaternion((0.1, -2.0, -0.3, 2.0)))

        for i in range(55):
            tc_channel.time_codes.append(tc_datum)

        tc_channel.num_time_codes = len(tc_channel.time_codes)

        for i in range(31):
            expected.time_coded_channels.append(tc_channel)

        tcb_channel = TimeCodedBitChannel(
            pivot=52,
            type=0,
            default_value=12,
            time_codes=[])

        tcb_datum = TimeCodedBitDatum(
            time_code=4,
            value=False)

        for i in range(55):
            tcb_channel.time_codes.append(tcb_datum)

        tcb_channel.num_time_codes = len(tcb_channel.time_codes)

        for i in range(31):
            expected.time_coded_bit_channels.append(tcb_channel)

        self.assertEqual(41964, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.header.version, actual.header.version)
        self.assertEqual(expected.header.name, actual.header.name)
        self.assertEqual(expected.header.hierarchy_name, actual.header.hierarchy_name)
        self.assertEqual(expected.header.num_frames, actual.header.num_frames)
        self.assertEqual(expected.header.frame_rate, actual.header.frame_rate)
        self.assertEqual(expected.header.flavor, actual.header.flavor)

        self.assertEqual(len(expected.time_coded_channels), len(actual.time_coded_channels))
        self.assertEqual(len(expected.time_coded_bit_channels), len(actual.time_coded_bit_channels))

        for i, chan in enumerate(expected.time_coded_channels):
            act = actual.time_coded_channels[i]
            self.assertEqual(chan.num_time_codes, act.num_time_codes)
            self.assertEqual(chan.pivot, act.pivot)
            self.assertEqual(chan.vector_len, act.vector_len)
            self.assertEqual(chan.type, act.type)

            self.assertEqual(len(chan.time_codes), len(act.time_codes))

            for j, time_code in enumerate(chan.time_codes):
                self.assertEqual(time_code.time_code, act.time_codes[j].time_code)
                self.assertAlmostEqual(time_code.value, act.time_codes[j].value, 5)

        for i, chan in enumerate(expected.time_coded_bit_channels):
            act = actual.time_coded_bit_channels[i]
            self.assertEqual(chan.num_time_codes, act.num_time_codes)
            self.assertEqual(chan.pivot, act.pivot)
            self.assertEqual(chan.type, act.type)
            self.assertAlmostEqual(chan.default_value, act.default_value, 5)

            self.assertEqual(len(chan.time_codes), len(act.time_codes))

            for j, time_code in enumerate(chan.time_codes):
                self.assertEqual(time_code.time_code, act.time_codes[j].time_code)
                self.assertAlmostEqual(time_code.value, act.time_codes[j].value, 5)

    def test_write_read_minimal(self):
        expected = CompressedAnimation(
            time_coded_channels=[],
            adaptive_delta_channels=[],
            time_coded_bit_channels=[],
            motion_channels=[])

        expected.header = CompressedAnimationHeader(
            version=Version(major=4, minor=1),
            name="CompAniHead",
            hierarchy_name="HieraName",
            num_frames=155,
            frame_rate=300,
            flavor=0)

        self.assertEqual(44, expected.header.size_in_bytes())
        self.assertEqual(52, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.header.version, actual.header.version)
        self.assertEqual(expected.header.name, actual.header.name)
        self.assertEqual(expected.header.hierarchy_name, actual.header.hierarchy_name)
        self.assertEqual(expected.header.num_frames, actual.header.num_frames)
        self.assertEqual(expected.header.frame_rate, actual.header.frame_rate)
        self.assertEqual(expected.header.flavor, actual.header.flavor)

        self.assertEqual(len(expected.time_coded_channels), len(actual.time_coded_channels))
        self.assertEqual(len(expected.adaptive_delta_channels), len(actual.adaptive_delta_channels))
        self.assertEqual(len(expected.time_coded_bit_channels), len(actual.time_coded_bit_channels))
        self.assertEqual(len(expected.motion_channels), len(actual.motion_channels))

