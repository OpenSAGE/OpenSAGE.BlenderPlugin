# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from tests.common.helpers.collision_box import *
from tests.utils import TestCase


class TestCollisionBox(TestCase):
    def test_write_read(self):
        expected = get_collision_box()

        self.assertEqual(68, expected.size(False))
        self.assertEqual(76, expected.size())

        self.write_read_test(expected, W3D_CHUNK_BOX, CollisionBox.read, compare_collision_boxes)

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
        self.write_read_xml_test(get_collision_box( xml=True), 'W3DCollisionBox', CollisionBox.parse,
                                 compare_collision_boxes, self)
