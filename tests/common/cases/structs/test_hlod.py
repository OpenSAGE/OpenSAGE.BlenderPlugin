# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.hlod import *
from tests.utils import TestCase
from unittest.mock import patch, call


class TestHLod(TestCase):
    def test_write_read(self):
        expected = get_hlod()

        self.assertEqual(48, expected.header.size())
        self.assertEqual(912, expected.size(False))
        self.assertEqual(920, expected.size())

        self.write_read_test(expected, W3D_CHUNK_HLOD, HLod.read, compare_hlods, self, True)

    def test_write_read_4_levels(self):
        expected = get_hlod_4_levels()

        self.assertEqual(48, expected.header.size())
        self.assertEqual(672, expected.size(False))
        self.assertEqual(680, expected.size())

        self.write_read_test(expected, W3D_CHUNK_HLOD, HLod.read, compare_hlods, self, True)

    def test_validate(self):
        hlod = get_hlod()
        self.file_format = 'W3D'
        self.assertTrue(hlod.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(hlod.validate(self))

        hlod.lod_arrays[0].sub_objects[0].identifier = 'containerName.tooooolongsuObjname'
        self.file_format = 'W3D'
        self.assertFalse(hlod.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(hlod.validate(self))

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_HLOD, output, 26, has_sub_chunks=True)

        write_chunk_head(W3D_CHUNK_HLOD_LOD_ARRAY,
                         output, 9, has_sub_chunks=True)
        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_HLOD, chunk_type)

        with (patch.object(self, 'warning')) as report_func:
            HLod.read(self, io_stream, subchunk_end)
            report_func.assert_called_with('unknown chunk_type in io_stream: 0x0')

    def test_name(self):
        sub_object = get_hlod_sub_object()

        self.assertEqual('containerName.default', sub_object.identifier)
        self.assertEqual('default', sub_object.name)

    def test_chunk_sizes(self):
        hlod = get_hlod_minimal()

        self.assertEqual(40, hlod.header.size(False))
        self.assertEqual(48, hlod.header.size())

        self.assertEqual(8, hlod.lod_arrays[0].header.size(False))
        self.assertEqual(16, hlod.lod_arrays[0].header.size())

        self.assertEqual(36, hlod.lod_arrays[0].sub_objects[0].size(False))
        self.assertEqual(44, hlod.lod_arrays[0].sub_objects[0].size())

        self.assertEqual(60, hlod.lod_arrays[0].size(False))
        self.assertEqual(68, hlod.lod_arrays[0].size())

        self.assertEqual(60, hlod.aggregate_array.size(False))
        self.assertEqual(68, hlod.aggregate_array.size())

        self.assertEqual(60, hlod.proxy_array.size(False))
        self.assertEqual(68, hlod.proxy_array.size())

        self.assertEqual(252, hlod.size(False))
        self.assertEqual(260, hlod.size())

    def test_write_read_xml(self):
        self.write_read_xml_test(get_hlod(), 'W3DContainer', HLod.parse, compare_hlods, self)

    def test_write_read_minimal_xml(self):
        self.write_read_xml_test(get_hlod_minimal(), 'W3DContainer', HLod.parse, compare_hlods, self)

    def test_parse_invalid_identifier(self):
        root = create_root()
        xml_hlod = create_node(root, 'W3DContainer')
        xml_hlod.set('id', 'fakeIdentifier')
        xml_hlod.set('Hierarchy', 'fakeHierarchy')

        create_node(xml_hlod, 'InvalidIdentifier')
        sub_object = create_node(xml_hlod, 'SubObject')
        sub_object.set('SubObjectID', 'fakeID')
        sub_object.set('BoneIndex', '2')
        create_node(sub_object, 'InvalidIdentifier')
        obj = create_node(sub_object, 'RenderObject')
        create_node(obj, 'InvalidIdentifier')

        xml_objects = root.findall('W3DContainer')
        self.assertEqual(1, len(xml_objects))

        with (patch.object(self, 'warning')) as report_func:
            HLod.parse(self, xml_objects[0])

            report_func.assert_has_calls([call('unhandled node \'InvalidIdentifier\' in W3DContainer!'),
                                          call('unhandled node \'InvalidIdentifier\' in W3DContainer SubObject!'),
                                          call('unhandled node \'InvalidIdentifier\' in W3DContainer RenderObject!')])
