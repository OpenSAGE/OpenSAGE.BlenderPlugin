# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from xml.dom import minidom

from tests.utils import *
from io_mesh_w3d.w3x.structs.hierarchy import *
from tests.w3x.helpers.hierarchy import *


class TestHierarchyW3X(W3dTestCase):
    def test_write_read(self):
        expected = get_hierarchy()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_hierarchies = dom.getElementsByTagName('W3DHierarchy')
        self.assertEqual(1, len(xml_hierarchies))

        actual = Hierarchy.parse(xml_hierarchies[0])
        compare_hierarchies(self, expected, actual)


    def test_write_read_minimal(self):
        expected = get_hierarchy_minimal()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_hierarchies = dom.getElementsByTagName('W3DHierarchy')
        self.assertEqual(1, len(xml_hierarchies))

        actual = Hierarchy.parse(xml_hierarchies[0])
        compare_hierarchies(self, expected, actual)
