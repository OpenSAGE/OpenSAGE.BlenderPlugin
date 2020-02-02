# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import unittest

from io_mesh_w3d.w3x.io_xml import *

from tests.utils import *
from tests.mathutils import *


class FakeStruct():
    def create(self, parent):
        obj = create_node(parent, 'obj')


class TestIOXML(TestCase):
    def test_create_node(self):
        root = ET.Element('root')
        create_node(root, 'child')

        self.assertIsNotNone(root.find('child'))

    def test_write_struct(self):
        expected = [
            '<?xml version="1.0" ?>\n',
            '<AssetDeclaration xmlns="uri:ea.com:eala:asset" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n',
            '   <obj/>\n',
            '</AssetDeclaration>\n']

        write_struct(FakeStruct(), self.outpath() + 'test.xml')

        file = open(self.outpath() + 'test.xml', mode='r')
        actual = file.readlines()
        file.close()

        self.assertEqual(len(expected), len(actual))
        for i, exp in enumerate(expected):
            self.assertEqual(exp, actual[i])

    def test_write(self):
        expected = [
            '<?xml version="1.0" ?>\n',
            '<AssetDeclaration xmlns="uri:ea.com:eala:asset" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/>\n']

        write(create_root(), self.outpath() + 'test.xml')

        file = open(self.outpath() + 'test.xml', mode='r')
        actual = file.readlines()
        file.close()

        self.assertEqual(expected, actual)
        self.assertEqual(len(expected), len(actual))
        for i, exp in enumerate(expected):
            self.assertEqual(exp, actual[i])

    def test_find_root(self):
        data = '<?xml version="1.0"?><AssetDeclaration xmlns="uri:ea.com:eala:asset" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"></AssetDeclaration>'
        file = open(self.outpath() + 'test.xml', 'w')
        file.write(data)
        file.close()

        root = find_root(self, self.outpath() + 'test.xml')
        self.assertIsNotNone(root)

    def test_find_root_none_found(self):
        data = '<?xml version="1.0"?><root></root>'
        file = open(self.outpath() + 'test.xml', 'w')
        file.write(data)
        file.close()

        root = find_root(self, self.outpath() + 'test.xml')
        self.assertIsNone(root)

    def test_create_root(self):
        root = create_root()

        self.assertEqual('AssetDeclaration', root.tag)
        self.assertEqual('uri:ea.com:eala:asset', root.get('xmlns'))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', root.get('xmlns:xsi'))

    def test_parse_value(self):
        expected = 3.14
        data = '<?xml version="1.0"?><root><object>3.14</object></root>'
        root = ET.fromstring(data)

        obj = root.find('object')
        actual = parse_value(obj, float)
        self.assertEqual(expected, actual)

    def test_create_value_(self):
        expected = '3.14'
        root = ET.Element('root')
        create_value(expected, root, 'object')

        actual = root.find('object')
        self.assertEqual(expected, actual.text)

    def test_parse_objects(self):
        expected = [3.14, 2.14, 1.14, 0.14]
        data = '<?xml version="1.0"?><root><o>3.14</o><o>2.14</o><o>1.14</o><o>0.14</o></root>'
        root = ET.fromstring(data)

        actual = parse_objects(root, 'o', parse_value, float)
        self.assertEqual(expected, actual)

    def test_create_object_list(self):
        values = [3.14, 2.14, 1.14, 0.14]

        root = ET.Element('root')
        create_object_list(root, 'objects', values, create_value, 'o')

        for i, child in enumerate(root.findall('o')):
            self.assertEqual(values[i], float(child.text))

    def test_parse_vector2(self):
        expected = get_vec2(x=2.01, y=3.14)
        data = '<?xml version="1.0"?><root><Vector X="2.01" Y="3.14"/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector2(vec)
        self.assertEqual(expected, actual)

    def test_parse_vector2_no_attributes(self):
        expected = get_vec2()
        data = '<?xml version="1.0"?><root><Vector/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector2(vec)
        self.assertEqual(expected, actual)

    def test_create_vector2(self):
        expected = get_vec()
        root = ET.Element('root')
        create_vector2(expected, root, 'Vector')

        actual = root.find('Vector')
        self.assertEqual(expected.x, float(actual.get('X')))
        self.assertEqual(expected.y, float(actual.get('Y')))

    def test_parse_vector(self):
        expected = get_vec(x=2.01, y=3.14, z=-0.33)
        data = '<?xml version="1.0"?><root><Vector X="2.01" Y="3.14" Z="-0.33"/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector(vec)
        self.assertEqual(expected, actual)

    def test_parse_vector_no_attributes(self):
        expected = get_vec()
        data = '<?xml version="1.0"?><root><Vector/></root>'
        root = ET.fromstring(data)

        vec = root.find('Vector')
        actual = parse_vector(vec)
        self.assertEqual(expected, actual)

    def test_create_vector(self):
        expected = get_vec()
        root = ET.Element('root')
        create_vector(expected, root, 'Vector')

        actual = root.find('Vector')
        self.assertEqual(expected.x, float(actual.get('X')))
        self.assertEqual(expected.y, float(actual.get('Y')))
        self.assertEqual(expected.z, float(actual.get('Z')))

    def test_parse_quaternion(self):
        expected = get_quat(w=67, x=2.01, y=3.14, z=-0.33)
        data = '<?xml version="1.0"?><root><Rotation W="67" X="2.01" Y="3.14" Z="-0.33"/></root>'
        root = ET.fromstring(data)

        quat = root.find('Rotation')
        actual = parse_quaternion(quat)
        self.assertEqual(expected, actual)

    def test_parse_quaternion_no_attributes(self):
        expected = get_quat()
        data = '<?xml version="1.0"?><root><Rotation/></root>'
        root = ET.fromstring(data)

        quat = root.find('Rotation')
        actual = parse_quaternion(quat)
        self.assertEqual(expected, actual)

    def test_create_vector(self):
        expected = get_quat()
        root = ET.Element('root')
        create_quaternion(expected, root, 'Rotation')

        actual = root.find('Rotation')
        self.assertEqual(expected.w, float(actual.get('W')))
        self.assertEqual(expected.x, float(actual.get('X')))
        self.assertEqual(expected.y, float(actual.get('Y')))
        self.assertEqual(expected.z, float(actual.get('Z')))

    def test_parse_matrix(self):
        expected = get_mat()
        data = '<?xml version="1.0"?><root><FixupMatrix M00="1" M01="0" M02="0" M03="0" M10="0" M11="1" M12="0" M13="0" M20="0" M21="0" M22="1" M23="0"/></root>'
        root = ET.fromstring(data)

        mat = root.find('FixupMatrix')
        actual = parse_matrix(mat)
        compare_mats(self, expected, actual)

    def test_parse_matrix_no_attributes(self):
        expected = get_mat()
        data = '<?xml version="1.0"?><root><FixupMatrix/></root>'
        root = ET.fromstring(data)

        mat = root.find('FixupMatrix')
        actual = parse_matrix(mat)
        compare_mats(self, expected, actual)

    def test_create_matrix(self):
        expected = get_mat()
        root = ET.Element('root')
        create_matrix(expected, root, 'FixupMatrix')

        actual = root.find('FixupMatrix')
        self.assertEqual(expected[0][0], float(actual.get('M00')))
        self.assertEqual(expected[0][1], float(actual.get('M01')))
        self.assertEqual(expected[0][2], float(actual.get('M02')))
        self.assertEqual(expected[0][3], float(actual.get('M03')))

        self.assertEqual(expected[1][0], float(actual.get('M10')))
        self.assertEqual(expected[1][1], float(actual.get('M11')))
        self.assertEqual(expected[1][2], float(actual.get('M12')))
        self.assertEqual(expected[1][3], float(actual.get('M13')))

        self.assertEqual(expected[2][0], float(actual.get('M20')))
        self.assertEqual(expected[2][1], float(actual.get('M21')))
        self.assertEqual(expected[2][2], float(actual.get('M22')))
        self.assertEqual(expected[2][3], float(actual.get('M23')))
