# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import unittest

from io_mesh_w3d.w3x.io_xml import *

from tests.utils import *
from tests.mathutils import *


class TestIOXML(TestCase):
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

######################### new stuff

    def test_parse_vector2_(self):
        expected = get_vec2(x=2.01, y=3.14)
        data = '<?xml version="1.0"?><root><Vector X="2.01" Y="3.14"/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector2_(vec)
        self.assertEqual(expected, actual)


    def test_parse_vector2_no_attributes(self):
        expected = get_vec2()
        data = '<?xml version="1.0"?><root><Vector/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector2_(vec)
        self.assertEqual(expected, actual)


    def test_create_vector2_(self):
        expected = get_vec()
        root = ET.Element('root')
        create_vector2_(expected, root, 'Vector')

        actual = root.find('Vector')
        self.assertEqual(expected.x, actual.get('X'))
        self.assertEqual(expected.y, actual.get('Y'))


    def test_parse_vector_(self):
        expected = get_vec(x=2.01, y=3.14, z=-0.33)
        data = '<?xml version="1.0"?><root><Vector X="2.01" Y="3.14" Z="-0.33"/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector_(vec)
        self.assertEqual(expected, actual)


    def test_parse_vector_no_attributes(self):
        expected = get_vec()
        data = '<?xml version="1.0"?><root><Vector/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector_(vec)
        self.assertEqual(expected, actual)


    def test_create_vector_(self):
        expected = get_vec()
        root = ET.Element('root')
        create_vector_(expected, root, 'Vector')

        actual = root.find('Vector')
        self.assertEqual(expected.x, actual.get('X'))
        self.assertEqual(expected.y, actual.get('Y'))
        self.assertEqual(expected.z, actual.get('Z'))


    def test_parse_quaternion_(self):
        expected = get_quat(w=67, x=2.01, y=3.14, z=-0.33)
        data = '<?xml version="1.0"?><root><Rotation W="67" X="2.01" Y="3.14" Z="-0.33"/></root>'
        root = ET.fromstring(data)

        quat = root.find('Rotation')
        actual = parse_quaternion_(quat)
        self.assertEqual(expected, actual)


    def test_parse_quaternion_no_attributes(self):
        expected = get_quat()
        data = '<?xml version="1.0"?><root><Rotation/></root>'
        root = ET.fromstring(data)

        quat = root.find('Rotation')
        actual = parse_quaternion_(quat)
        self.assertEqual(expected, actual)


    def test_create_vector_(self):
        expected = get_quat()
        root = ET.Element('root')
        create_quaternion_(expected, root, 'Rotation')

        actual = root.find('Rotation')
        self.assertEqual(expected.w, actual.get('W'))
        self.assertEqual(expected.x, actual.get('X'))
        self.assertEqual(expected.y, actual.get('Y'))
        self.assertEqual(expected.z, actual.get('Z'))


    def test_parse_matrix_(self):
        expected = get_mat()
        data = '<?xml version="1.0"?><root><FixupMatrix M00="1" M01="0" M02="0" M03="0" M10="0" M11="1" M12="0" M13="0" M20="0" M21="0" M22="1" M23="0"/></root>'
        root = ET.fromstring(data)

        quat = root.find('FixupMatrix')
        actual = parse_matrix_(quat)
        compare_mats(self, expected, actual)


    def test_parse_matrix_no_attributes(self):
        expected = get_mat()
        data = '<?xml version="1.0"?><root><FixupMatrix/></root>'
        root = ET.fromstring(data)

        mat = root.find('FixupMatrix')
        actual = parse_matrix_(mat)
        compare_mats(self, expected, actual)


    def test_create_matrix_(self):
        expected = get_mat()
        root = ET.Element('root')
        create_matrix_(expected, root, 'FixupMatrix')

        actual = root.find('FixupMatrix')
        self.assertEqual(expected[0][0], actual.get('M00'))
        self.assertEqual(expected[0][1], actual.get('M01'))
        self.assertEqual(expected[0][2], actual.get('M02'))
        self.assertEqual(expected[0][3], actual.get('M03'))

        self.assertEqual(expected[1][0], actual.get('M10'))
        self.assertEqual(expected[1][1], actual.get('M11'))
        self.assertEqual(expected[1][2], actual.get('M12'))
        self.assertEqual(expected[1][3], actual.get('M13'))

        self.assertEqual(expected[2][0], actual.get('M20'))
        self.assertEqual(expected[2][1], actual.get('M21'))
        self.assertEqual(expected[2][2], actual.get('M22'))
        self.assertEqual(expected[2][3], actual.get('M23'))

