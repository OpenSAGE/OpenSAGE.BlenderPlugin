# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import unittest
import io
import struct
from tests.test_utils import *
from io_mesh_w3d.io_binary import *


class TestIOBinary(unittest.TestCase):
    def test_read_string(self):
        expecteds = [
            "Teststring",
            "Blender Plugin For W3D"]

        for expected in expecteds:
            f = io.BytesIO(bytes(expected, 'UTF-8') + struct.pack('B', 0b0))
            self.assertEqual(expected, read_string(f))

    def test_read_fixed_string(self):
        inputs = [
            "Teststring",
            "Blender Plugin For W3D"]

        expecteds = [
            "Teststring",
            "Blender Plugin F"]

        for i, expected in enumerate(expecteds):
            f = io.BytesIO(bytes(inputs[i], 'UTF-8') + struct.pack('B', 0b0))
            self.assertEqual(expected, read_fixed_string(f))

    def test_read_long_fixed_string(self):
        inputs = [
            "Teststring",
            "Blender Plugin For W3D meshes animations and hierarchy"]

        expecteds = [
            "Teststring",
            "Blender Plugin For W3D meshes an"]

        for i, expected in enumerate(expecteds):
            f = io.BytesIO(bytes(inputs[i], 'UTF-8') + struct.pack('B', 0b0))
            self.assertEqual(expected, read_long_fixed_string(f))

    def test_read_long(self):
        inputs = [0, 1, 200, 999999, 123456, -5, -500]

        for inp in inputs:
            f = io.BytesIO(struct.pack("<l", inp))
            self.assertEqual(inp, read_long(f))

    def test_read_ulong(self):
        inputs = [0, 1, 200, 999999, 123456, 5, 500]

        for inp in inputs:
            f = io.BytesIO(struct.pack("<L", inp))
            self.assertEqual(inp, read_ulong(f))

    def test_read_short(self):
        inputs = [0, 1, 200, -32767, 32767, -5, -500]

        for inp in inputs:
            f = io.BytesIO(struct.pack("<h", inp))
            self.assertEqual(inp, read_short(f))

    def test_read_ushort(self):
        inputs = [0, 1, 200, 0xffff, 5, 500]

        for inp in inputs:
            f = io.BytesIO(struct.pack("<H", inp))
            self.assertEqual(inp, read_ushort(f))

    def test_read_float(self):
        inputs = [0, 1, 200, 999999, 123456, 5, 500,
                  0.0, 2.0, 3.14, -22.900, 0.0000001]

        for inp in inputs:
            f = io.BytesIO(struct.pack("<f", inp))
            self.assertAlmostEqual(inp, read_float(f), 5)


runTestCases([TestIOBinary])
