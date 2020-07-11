# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import unittest

from io_mesh_w3d.w3d.io_binary import *
from tests.mathutils import *
from tests.utils import TestCase


class TestIOBinary(TestCase):
    def test_read_string(self):
        expecteds = [
            'Teststring',
            'Blender Plugin For W3D this is a veeery long string for this test']

        for expected in expecteds:
            io_stream = io.BytesIO(
                bytes(expected, 'UTF-8') + struct.pack('B', 0b0))
            self.assertEqual(expected, read_string(io_stream))

    def test_write_string(self):
        expecteds = [
            'Teststring',
            'Blender Plugin For W3D this is a veeeeery long string for this test']

        for expected in expecteds:
            io_stream = io.BytesIO()
            write_string(expected, io_stream)

            self.assertEqual(expected + '\x00',
                             io_stream.getvalue().decode('utf-8'))

    def test_read_fixed_string(self):
        inputs = [
            'Teststring',
            'Blender Plugin For W3D']

        expecteds = [
            'Teststring',
            'Blender Plugin F']

        for i, expected in enumerate(expecteds):
            io_stream = io.BytesIO(
                bytes(inputs[i], 'UTF-8') + struct.pack('B', 0b0))
            self.assertEqual(expected, read_fixed_string(io_stream))

    def test_write_fixed_string(self):
        inputs = [
            'Teststring',
            'Blender Plugin For W3D this is a veeeeery long string for this test']

        expecteds = [
            'Teststring',
            'Blender Plugin F']

        for i, expected in enumerate(expecteds):
            io_stream = io.BytesIO()
            write_fixed_string(inputs[i], io_stream)

            while len(expected) < STRING_LENGTH:
                expected += '\x00'

            self.assertEqual(expected, io_stream.getvalue().decode('utf-8'))

    def test_read_long_fixed_string(self):
        inputs = [
            'Teststring',
            'Blender Plugin For W3D meshes animations and hierarchy']

        expecteds = [
            'Teststring',
            'Blender Plugin For W3D meshes an']

        for i, expected in enumerate(expecteds):
            io_stream = io.BytesIO(
                bytes(inputs[i], 'UTF-8') + struct.pack('B', 0b0))
            self.assertEqual(expected, read_long_fixed_string(io_stream))

    def test_write_long_fixed_string(self):
        inputs = [
            'Teststring',
            'Blender Plugin For W3D this is a veeeeery long string for this test']

        expecteds = [
            'Teststring',
            'Blender Plugin For W3D this is a']

        for i, expected in enumerate(expecteds):
            io_stream = io.BytesIO()
            write_long_fixed_string(inputs[i], io_stream)

            while len(expected) < LARGE_STRING_LENGTH:
                expected += '\x00'

            self.assertEqual(expected, io_stream.getvalue().decode('utf-8'))

    def test_read_long(self):
        inputs = [0, 1, 200, 999999, 123456, -5, -500]

        for inp in inputs:
            io_stream = io.BytesIO(struct.pack('<l', inp))
            self.assertEqual(inp, read_long(io_stream))

    def test_write_long(self):
        inputs = [0, 1, 200, 999999, 123456, -5, -500]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_long(inp, io_stream)
            self.assertEqual(inp, struct.unpack('<l', io_stream.getvalue())[0])

    def test_read_ulong(self):
        inputs = [0, 1, 200, 999999, 123456, 5, 500]

        for inp in inputs:
            io_stream = io.BytesIO(struct.pack('<L', inp))
            self.assertEqual(inp, read_ulong(io_stream))

    def test_write_ulong(self):
        inputs = [0, 1, 200, 999999, 123456, 5, 500]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_ulong(inp, io_stream)
            self.assertEqual(inp, struct.unpack('<L', io_stream.getvalue())[0])

    def test_read_short(self):
        inputs = [0, 1, 200, -32767, 32767, -5, -500]

        for inp in inputs:
            io_stream = io.BytesIO(struct.pack('<h', inp))
            self.assertEqual(inp, read_short(io_stream))

    def test_write_short(self):
        inputs = [0, 1, 200, -32768, 32767, -5, -500]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_short(inp, io_stream)
            self.assertEqual(inp, struct.unpack('<h', io_stream.getvalue())[0])

    def test_read_ushort(self):
        inputs = [0, 1, 200, 0xffff, 5, 500]

        for inp in inputs:
            io_stream = io.BytesIO(struct.pack('<H', inp))
            self.assertEqual(inp, read_ushort(io_stream))

    def test_write_ushort(self):
        inputs = [0, 1, 200, 0xffff, 5, 500]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_ushort(inp, io_stream)
            self.assertEqual(inp, struct.unpack('<H', io_stream.getvalue())[0])

    def test_read_float(self):
        inputs = [0, 1, 200, 999999, 123456, 5, 500,
                  0.0, 2.0, 3.14, -22.900, 0.0000001]

        for inp in inputs:
            io_stream = io.BytesIO(struct.pack('<f', inp))
            self.assertAlmostEqual(inp, read_float(io_stream), 5)

    def test_write_float(self):
        inputs = [0, 1, 200, 999999, 123456, 5, 500,
                  0.0, 2.0, 3.14, -22.900, 0.0000001]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_float(inp, io_stream)
            self.assertAlmostEqual(inp, struct.unpack(
                '<f', io_stream.getvalue())[0], 5)

    def test_read_byte(self):
        inputs = [0, 1, 127, -66, 123, 55, 000,
                  111, -128, 33]

        for inp in inputs:
            io_stream = io.BytesIO(struct.pack('<b', inp))
            self.assertEqual(inp, read_byte(io_stream))

    def test_write_byte(self):
        inputs = [0, 1, 20, 77, 123, -128, 000,
                  111, 127, -33]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_byte(inp, io_stream)
            self.assertEqual(inp, struct.unpack('<b', io_stream.getvalue())[0])

    def test_read_ubyte(self):
        inputs = [0, 1, 200, 255, 123, 55, 000,
                  111, 222, 33]

        for inp in inputs:
            io_stream = io.BytesIO(struct.pack('<B', inp))
            self.assertEqual(inp, read_ubyte(io_stream))

    def test_write_ubyte(self):
        inputs = [0, 1, 200, 255, 123, 55, 000,
                  111, 222, 33]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_ubyte(inp, io_stream)
            self.assertEqual(inp, struct.unpack('<B', io_stream.getvalue())[0])

    def test_read_vector(self):
        inputs = [get_vec(), get_vec(1, 2, 3)]

        for inp in inputs:
            data = struct.pack('<f', inp.x)
            data += struct.pack('<f', inp.y)
            data += struct.pack('<f', inp.z)
            io_stream = io.BytesIO(data)

            compare_vectors(self, inp, read_vector(io_stream))

    def test_write_vector(self):
        inputs = [get_vec(), get_vec(1, 2, 3)]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_vector(inp, io_stream)

            data = io_stream.getvalue()
            x = struct.unpack('<f', data[0:4])[0]
            y = struct.unpack('<f', data[4:8])[0]
            z = struct.unpack('<f', data[8:12])[0]

            compare_vectors(self, inp, get_vec(x, y, z))

    def test_read_quaternion(self):
        inputs = [get_quat(), get_quat(0, 1, 2, 3)]

        for inp in inputs:
            data = struct.pack('<f', inp.x)
            data += struct.pack('<f', inp.y)
            data += struct.pack('<f', inp.z)
            data += struct.pack('<f', inp.w)
            io_stream = io.BytesIO(data)

            compare_quats(self, inp, read_quaternion(io_stream))

    def test_write_quaternion(self):
        inputs = [get_quat(0, 0, 0, 0), get_quat(0, 1, 2, 3)]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_quaternion(inp, io_stream)

            data = io_stream.getvalue()
            x = struct.unpack('<f', data[0:4])[0]
            y = struct.unpack('<f', data[4:8])[0]
            z = struct.unpack('<f', data[8:12])[0]
            w = struct.unpack('<f', data[12:16])[0]

            compare_quats(self, inp, get_quat(w, x, y, z))

    def test_read_vector2(self):
        inputs = [get_vec2(), get_vec2(1, 2)]

        for inp in inputs:
            data = struct.pack('<f', inp.x)
            data += struct.pack('<f', inp.y)
            io_stream = io.BytesIO(data)

            compare_vectors2(self, inp, read_vector2(io_stream))

    def test_write_vector2(self):
        inputs = [get_vec2(), get_vec2(1, 2)]

        for inp in inputs:
            io_stream = io.BytesIO()
            write_vector2(inp, io_stream)

            data = io_stream.getvalue()
            x = struct.unpack('<f', data[0:4])[0]
            y = struct.unpack('<f', data[4:8])[0]

            compare_vectors2(self, inp, get_vec2(x, y))

    def test_read_channel_value(self):
        inputs = [(0, 1.0), (1, 2.0), (3, 4.0), (6, get_quat(1, 2, 3, 4))]

        for inp in inputs:
            if inp[0] <= 3:
                data = struct.pack('<f', inp[1])
                io_stream = io.BytesIO(data)
                self.assertAlmostEqual(
                    inp[1], read_channel_value(io_stream, inp[0]), 5)
            else:
                data = struct.pack('<f', inp[1].x)
                data += struct.pack('<f', inp[1].y)
                data += struct.pack('<f', inp[1].z)
                data += struct.pack('<f', inp[1].w)
                io_stream = io.BytesIO(data)
                compare_quats(
                    self, inp[1], read_channel_value(io_stream, inp[0]))

    def test_write_channel_value(self):
        inputs = [(0, 1.0), (1, 2.0), (3, 4.0),
                  (6, get_quat(1.0, 2.0, 3.0, 4.0))]

        for inp in inputs:
            type = inp[0]
            io_stream = io.BytesIO()
            write_channel_value(inp[1], io_stream, type)
            data = io_stream.getvalue()
            if type == 6:
                self.assertEqual(inp[1].x, struct.unpack('<f', data[0:4])[0])
                self.assertEqual(inp[1].y, struct.unpack('<f', data[4:8])[0])
                self.assertEqual(inp[1].z, struct.unpack('<f', data[8:12])[0])
                self.assertEqual(inp[1].w, struct.unpack('<f', data[12:16])[0])
            else:
                self.assertEqual(inp[1], struct.unpack('<f', data[0:4])[0])

    def test_read_chunk_head(self):
        inputs = [(0, 200), (255, 500), (255, 0xFFFFFFFF)]
        expecteds = [(0, 200, 208), (255, 500, 508),
                     (255, 0x7FFFFFFF, 0x80000007)]

        for i, inp in enumerate(inputs):
            c_type = struct.pack('<L', inp[0])
            c_size = struct.pack('<L', inp[1])
            io_stream = io.BytesIO(c_type + c_size)

            (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
            self.assertEqual(expecteds[i][0], chunkType)
            self.assertEqual(expecteds[i][1], chunkSize)
            self.assertEqual(expecteds[i][2], chunkEnd)

    def test_write_chunk_head(self):
        inputs = [(0, 200, False), (255, 500, False), (255, 0xFF, True)]
        expecteds = [(0, 200), (255, 500), (255, 0x800000FF)]

        for i, inp in enumerate(inputs):
            io_stream = io.BytesIO()
            write_chunk_head(inp[0], io_stream, inp[1], inp[2])
            io_stream.seek(0)
            chunk_type = struct.unpack('<L', io_stream.read(4))[0]
            chunk_size = struct.unpack('<L', io_stream.read(4))[0]

            self.assertEqual(expecteds[i][0], chunk_type)
            self.assertEqual(expecteds[i][1], chunk_size)
