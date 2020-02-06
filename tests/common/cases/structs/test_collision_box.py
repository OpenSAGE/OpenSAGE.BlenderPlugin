# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.collision_box import *
from tests.utils import TestCase


class TestCollisionBox(TestCase):
    def test_write_read(self):
        expected = get_collision_box()

        self.assertEqual(68, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, _) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_BOX, chunkType)
        self.assertEqual(expected.size(), chunkSize)

        actual = CollisionBox.read(io_stream)
        compare_collision_boxes(self, expected, actual)

    def test_validate(self):
        box = get_collision_box()
        self.file_format = 'W3D'
        self.assertTrue(box.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(box.validate(self))

        box.name_ = 'containerNameeee.BOUNDINGBOX00000'
        self.file_format = 'W3D'
        self.assertFalse(box.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(box.validate(self))

    def test_name(self):
        box = get_collision_box()

        self.assertEqual('containerName.BOUNDINGBOX', box.name_)
        self.assertEqual('BOUNDINGBOX', box.name())

        box.name_ = 'BOUNDINGBOX'
        self.assertEqual('BOUNDINGBOX', box.name())

    def test_write_read_xml(self):
        self.write_read_xml_test(
            get_collision_box(
                xml=True),
            'W3DCollisionBox',
            CollisionBox.parse,
            compare_collision_boxes,
            self)
