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

        # TimeCodedChannels

        tc_channel = TimeCodedAnimationChannel(
            num_time_codes=55,
            pivot=4,
            vector_len=4,
            type=6,
            time_codes=[])

        tc_datum = TimeCodedDatum(
            time_code=34,
            non_interpolated=True,
            value=Quaternion((0.1, -2.0, -0.3, 2.0)))

        for _ in range(tc_channel.num_time_codes):
            tc_channel.time_codes.append(tc_datum)

        for _ in range(31):
            expected.time_coded_channels.append(tc_channel)


        # TimeCodedBitChannels

        tcb_channel = TimeCodedBitChannel(
            num_time_codes=55,
            pivot=52,
            type=0,
            default_value=12,
            time_codes=[])

        tcb_datum = TimeCodedBitDatum(
            time_code=1,
            value=True)

        for _ in range(tcb_channel.num_time_codes):
            tcb_channel.time_codes.append(tcb_datum)

        for _ in range(31):
            expected.time_coded_bit_channels.append(tcb_channel)

        # TimeCodedBitChannels

        m_channel_tc = MotionChannel(
            delta_type=0,
            vector_len=1,
            type=0,
            num_time_codes=55,
            pivot=182,
            data=[])

        datum = TimeCodedDatum(
            time_code=3,
            value=2.0)

        for _ in range(m_channel_tc.num_time_codes):
            m_channel_tc.data.append(datum)

        m_channel_ad4 = MotionChannel(
            delta_type=1,
            vector_len=1,
            type=0,
            num_time_codes=55,
            pivot=182,
            data=[])

        ad_motion_channel = AdaptiveDeltaMotionAnimationChannel(
            scale = 4.0,
            initial_value=-4.0,
            data=None)

        

        m_channel_ad8 = MotionChannel(
            delta_type=2,
            vector_len=1,
            type=0,
            num_time_codes=55,
            pivot=182,
            data=[])

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


    def test_write_read_adaptive_delta(self):
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
            flavor=1)

        self.assertEqual(44, expected.header.size_in_bytes())

        ad_channel = AdaptiveDeltaAnimationChannel(
            pivot=311,
            vector_len=1,
            type=2,
            scale=4,
            num_time_codes=1)

        ad_data = AdaptiveDeltaData(
            initial_value=2.0,
            bit_count=4,
            delta_blocks=[])

        ad_block = AdaptiveDeltaBlock(
            vector_index=7,
            block_index=9,
            delta_bytes=[])

        ad_block.delta_bytes = bytes([0x00,0x01,0x02,0x03,0x04,0x05,0x06])

        count = (ad_channel.num_time_codes + 15) >> 4

        for _ in range(count):
            for _ in range(ad_channel.vector_len):
                ad_data.delta_blocks.append(ad_block)

        ad_channel.data = ad_data

        for _ in range(66):
            expected.adaptive_delta_channels.append(ad_channel)

        self.assertEqual(2230, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_COMPRESSED_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        #actual = CompressedAnimation.read(self, io_stream, chunkEnd)
        #self.assertEqual(expected.header.version, actual.header.version)
        #self.assertEqual(expected.header.name, actual.header.name)
        #self.assertEqual(expected.header.hierarchy_name, actual.header.hierarchy_name)
        #self.assertEqual(expected.header.num_frames, actual.header.num_frames)
        #self.assertEqual(expected.header.frame_rate, actual.header.frame_rate)
        #self.assertEqual(expected.header.flavor, actual.header.flavor)

        #self.assertEqual(len(expected.adaptive_delta_channels), len(actual.adaptive_delta_channels))

        #for i, chan in enumerate(expected.adaptive_delta_channels):
        #    act = actual.adaptive_delta_channels[i]
        #    self.assertEqual(chan.num_time_codes, act.num_time_codes)
        #    self.assertEqual(chan.pivot, act.pivot)
         #   self.assertEqual(chan.vector_len, act.vector_len)
        #    self.assertEqual(chan.type, act.type)
        #    self.assertEqual(chan.scale, act.scale)

        #    self.assertEqual(chan.data.initial_value, act.data.initial_value)
        #    self.assertEqual(chan.data.bit_count, act.data.bit_count)

        #    self.assertEqual(len(chan.data.delta_blocks), len(act.data.delta_blocks))

        #    for j, block in enumerate(chan.data.delta_blocks):
        #        current = act.data.delta_blocks[j]
        #        self.assertEqual(block.vector_index, current.vector_index)
        #        self.assertEqual(block.block_index, current.block_index)

        #        self.assertEqual(len(block.delta_bytes), len(current.delta_bytes))
        #        self.assertEqual(block.delta_bytes, current.delta_bytes)


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

