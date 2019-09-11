# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import unittest
import io

from mathutils import Quaternion

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_animation import Animation, AnimationHeader, \
    AnimationChannel, W3D_CHUNK_ANIMATION
from io_mesh_w3d.io_binary import read_chunk_head


class TestAnimation(unittest.TestCase):
    def test_write_read(self):
        expected = Animation()
        expected.header = AnimationHeader(
            version=Version(major=4, minor=1),
            name="AniHeader",
            hierarchy_name="HieraName",
            num_frames=155,
            frame_rate=300)

        self.assertEqual(44, expected.header.size_in_bytes())

        x_channel = AnimationChannel(
            first_frame=1,
            last_frame=33,
            vector_len=1,
            type=3,
            pivot=33,
            unknown=123,
            data=[])

        for i in range(55):
            x_channel.data.append(2.0)

        expected.channels.append(x_channel)

        q_channel = AnimationChannel(
            first_frame=1,
            last_frame=33,
            vector_len=4,
            type=6,
            pivot=33,
            unknown=123,
            data=[])

        for i in range(55):
            q_channel.data.append(Quaternion((1.0, 2.0, 3.0, 4.0)))

        expected.channels.append(q_channel)

        self.assertEqual(1192, expected.size_in_bytes())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_ANIMATION, chunkType)
        self.assertEqual(expected.size_in_bytes(), chunkSize)

        actual = Animation.read(self, io_stream, chunkEnd)
        self.assertEqual(expected.header.version, actual.header.version)
        self.assertEqual(expected.header.name, actual.header.name)
        self.assertEqual(expected.header.hierarchy_name, actual.header.hierarchy_name)
        self.assertEqual(expected.header.num_frames, actual.header.num_frames)
        self.assertEqual(expected.header.frame_rate, actual.header.frame_rate)

        self.assertEqual(len(expected.channels), len(actual.channels))

        for i, chan in enumerate(expected.channels):
            act = actual.channels[i]
            self.assertEqual(chan.first_frame, act.first_frame)
            self.assertEqual(chan.last_frame, act.last_frame)
            self.assertEqual(chan.vector_len, act.vector_len)
            self.assertEqual(chan.type, act.type)
            self.assertEqual(chan.pivot, act.pivot)
            self.assertEqual(chan.unknown, act.unknown)

            self.assertEqual(len(chan.data), len(act.data))

            for j, d in enumerate(chan.data):
                self.assertEqual(d, act.data[j])
