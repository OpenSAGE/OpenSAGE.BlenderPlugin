# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.hierarchy import *
from tests.utils import TestCase
from unittest.mock import patch, call


class TestHierarchy(TestCase):
    def test_write_read(self):
        expected = get_hierarchy()

        self.assertEqual(44, expected.header.size())
        self.assertEqual(636, expected.size(False))
        self.assertEqual(644, expected.size())

        self.write_read_test(expected, W3D_CHUNK_HIERARCHY, Hierarchy.read, compare_hierarchies, self, True)

    def test_write_read_minimal(self):
        expected = get_hierarchy_minimal()

        self.assertEqual(44, expected.header.size())
        self.assertEqual(132, expected.size(False))
        self.assertEqual(140, expected.size())

        self.write_read_test(expected, W3D_CHUNK_HIERARCHY, Hierarchy.read, compare_hierarchies, self, True)

    def test_write_read_empty(self):
        expected = get_hierarchy_empty()

        self.assertEqual(44, expected.header.size())
        self.assertEqual(44, expected.size(False))
        self.assertEqual(52, expected.size())

        self.write_read_test(expected, W3D_CHUNK_HIERARCHY, Hierarchy.read, compare_hierarchies, self, True)

    def test_validate(self):
        hierarchy = get_hierarchy()
        self.file_format = 'W3D'
        self.assertTrue(hierarchy.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(hierarchy.validate(self))

        hierarchy.header.name = 'tooolonghieraname'
        self.file_format = 'W3D'
        self.assertFalse(hierarchy.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(hierarchy.validate(self))

        hierarchy = get_hierarchy()
        hierarchy.pivots[1].name = 'tooolongpivotname'
        self.file_format = 'W3D'
        self.assertFalse(hierarchy.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(hierarchy.validate(self))

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_HIERARCHY, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_HIERARCHY, chunk_type)

        with (patch.object(self, 'warning')) as report_func:
            Hierarchy.read(self, io_stream, subchunk_end)
            report_func.assert_called_with('unknown chunk_type in io_stream: 0x0')

    def test_chunk_sizes(self):
        hierarchy = get_hierarchy_minimal()

        self.assertEqual(36, hierarchy.header.size(False))
        self.assertEqual(44, hierarchy.header.size())

        self.assertEqual(60, list_size(hierarchy.pivots, False))

        self.assertEqual(12, vec_list_size(hierarchy.pivot_fixups, False))

        self.assertEqual(132, hierarchy.size(False))
        self.assertEqual(140, hierarchy.size())

    def test_write_read_xml(self):
        self.write_read_xml_test(get_hierarchy(xml=True), 'W3DHierarchy', Hierarchy.parse, compare_hierarchies, self)

    def test_write_read_minimal_xml(self):
        self.write_read_xml_test(get_hierarchy_minimal(xml=True), 'W3DHierarchy', Hierarchy.parse, compare_hierarchies,
                                 self)

    def test_create_parse_xml_pivot_name_is_None(self):
        hiera = get_hierarchy(xml=True)
        hiera.pivots[0].name = None
        self.write_read_xml_test(hiera, 'W3DHierarchy', Hierarchy.parse, compare_hierarchies, self)

    def test_parse_invalid_identifier(self):
        root = create_root()
        xml_hierarchy = create_node(root, 'W3DHierarchy')
        xml_hierarchy.set('id', 'fakeIdentifier')

        create_node(xml_hierarchy, 'InvalidIdentifier')
        pivot = create_node(xml_hierarchy, 'Pivot')
        pivot.set('Parent', '1')
        create_node(pivot, 'InvalidIdentifier')

        xml_objects = root.findall('W3DHierarchy')
        self.assertEqual(1, len(xml_objects))

        with (patch.object(self, 'warning')) as report_func:
            actual = Hierarchy.parse(self, xml_objects[0])

            report_func.assert_has_calls([call('unhandled node \'InvalidIdentifier\' in W3DHierarchy!'),
                                          call('unhandled node \'InvalidIdentifier\' in Pivot!')])
