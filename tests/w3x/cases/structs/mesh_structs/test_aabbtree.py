# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from xml.dom import minidom

from tests import utils

from io_mesh_w3d.w3x.structs.mesh_structs.aabbtree import *
from tests.w3x.helpers.mesh_structs.aabbtree import *


class TestAABBTreeW3X(utils.W3dTestCase):
    def test_write_read(self):
        expected = get_aabbtree()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_aabbtrees = dom.getElementsByTagName('AABTree')
        self.assertEqual(1, len(xml_aabbtrees))

        actual = AABBTree.parse(xml_aabbtrees[0])
        compare_aabbtrees(self, expected, actual)


    def test_write_read_minimal(self):
        expected = get_aabbtree_minimal()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_aabbtrees = dom.getElementsByTagName('AABTree')
        self.assertEqual(1, len(xml_aabbtrees))

        actual = AABBTree.parse(xml_aabbtrees[0])
        compare_aabbtrees(self, expected, actual)
