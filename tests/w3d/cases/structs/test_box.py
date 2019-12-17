# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import TestCase
from tests.helpers.w3d_box import *

from tests.w3d.helpers.box import get_box, compare_boxes

class TestBox(TestCase):
    def test_write_read(self):
        expected = get_box()

        self.assertEqual(68, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, _) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_BOX, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = Box.read(io_stream)
        compare_boxes(self, expected, actual)
