# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import unittest

from io_mesh_w3d.w3x.io_xml import *
from tests.mathutils import *


class TestIOXML(unittest.TestCase):
    def test_childs(self):
        doc = minidom.Document()
        parent = doc.createElement('PARENT')
        doc.appendChild(parent)

        parent.appendChild(doc.createElement('Valid'))
        parent.appendChild(doc.createComment('Invalid'))
        parent.appendChild(doc.createTextNode('hello, world!'))

        childs = parent.childs()
        self.assertEqual(1, len(childs))
        self.assertEqual('Valid', childs[0].tagName)
