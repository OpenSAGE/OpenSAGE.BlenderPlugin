# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from xml.dom import minidom

from tests import utils

from io_mesh_w3d.structs_w3x.w3x_mesh import *
from tests.helpers_w3x.w3x_mesh import *


class TestHierarchyW3X(utils.W3dTestCase):
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
