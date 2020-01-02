# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from xml.dom import minidom

from tests.utils import *

from io_mesh_w3d.w3x.structs.mesh import *
from tests.w3x.helpers.mesh import *


class TestHierarchyW3X(TestCase):
    def test_write_read(self):
        expected = get_mesh()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_meshes = dom.getElementsByTagName('W3DMesh')
        self.assertEqual(1, len(xml_meshes))

        actual = Mesh.parse(xml_meshes[0])
        compare_meshes(self, expected, actual)


    def test_write_read_minimal(self):
        expected = get_mesh_minimal()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_meshes = dom.getElementsByTagName('W3DMesh')
        self.assertEqual(1, len(xml_meshes))

        actual = Mesh.parse(xml_meshes[0])
        compare_meshes(self, expected, actual)
