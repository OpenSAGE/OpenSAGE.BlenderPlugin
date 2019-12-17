# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
import io

from xml.dom import minidom

from tests import utils

from io_mesh_w3d.w3x.structs.mesh_structs.fx_shader import *
from tests.w3x.helpers.mesh_structs.fx_shader import *


class TestFxShaderW3X(utils.W3dTestCase):
    def test_write_read(self):
        expected = get_fx_shader()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_fx_shaders = dom.getElementsByTagName('FXShader')
        self.assertEqual(1, len(xml_fx_shaders))

        actual = FXShader.parse(xml_fx_shaders[0])
        compare_fx_shaders(self, expected, actual)


    def test_write_read_minimal(self):
        expected = get_fx_shader_minimal()

        doc = minidom.Document()
        doc.appendChild(expected.create(doc))

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent = '   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_fx_shaders = dom.getElementsByTagName('FXShader')
        self.assertEqual(1, len(xml_fx_shaders))

        actual = FXShader.parse(xml_fx_shaders[0])
        compare_fx_shaders(self, expected, actual)