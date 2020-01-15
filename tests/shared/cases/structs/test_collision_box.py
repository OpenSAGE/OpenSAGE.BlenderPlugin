# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.shared.helpers.collision_box import *
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

    def test_name(self):
        box = get_collision_box()

        self.assertEqual("containerName.BOUNDINGBOX", box.name_)
        self.assertEqual("BOUNDINGBOX", box.name())

        box.name_ = "BOUNDINGBOX"
        self.assertEqual("BOUNDINGBOX", box.name())

    def test_write_read_xml(self):
        expected = get_collision_box(xml=True)

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_collision_boxes = dom.getElementsByTagName('W3DCollisionBox')
        self.assertEqual(1, len(xml_collision_boxes))

        actual = CollisionBox.parse(xml_collision_boxes[0])
        compare_collision_boxes(self, expected, actual)
