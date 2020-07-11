# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.common.helpers.animation import *
from tests.utils import TestCase
from unittest.mock import patch, call


class TestAnimation(TestCase):
    def test_write_read(self):
        expected = get_animation()

        self.assertEqual(52, expected.header.size())
        self.assertEqual(683, expected.size(False))
        self.assertEqual(691, expected.size())

        self.write_read_test(expected, W3D_CHUNK_ANIMATION, Animation.read, compare_animations, self, True)

    def test_write_read_empty(self):
        expected = get_animation_empty()

        self.assertEqual(52, expected.header.size())
        self.assertEqual(52, expected.size(False))
        self.assertEqual(60, expected.size())

        self.write_read_test(expected, W3D_CHUNK_ANIMATION, Animation.read, compare_animations, self, True)

    def test_unknown_chunk_skip(self):
        output = io.BytesIO()
        write_chunk_head(W3D_CHUNK_ANIMATION, output, 9, has_sub_chunks=True)

        write_chunk_head(0x00, output, 1, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        self.assertEqual(W3D_CHUNK_ANIMATION, chunk_type)

        with (patch.object(self, 'warning')) as report_func:
            Animation.read(self, io_stream, subchunk_end)
            report_func.assert_called_with('unknown chunk_type in io_stream: 0x0')

    def test_validate(self):
        ani = get_animation()
        self.file_format = 'W3D'
        self.assertTrue(ani.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(ani.validate(self))

        ani.header.name = 'tooooolonganiname'
        self.file_format = 'W3D'
        self.assertFalse(ani.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(ani.validate(self))

        ani = get_animation()
        ani.header.hierarchy_name = 'tooooolonganiname'
        self.file_format = 'W3D'
        self.assertFalse(ani.validate(self))
        self.file_format = 'W3X'
        self.assertTrue(ani.validate(self))

        ani = get_animation()
        ani.channels = []
        self.file_format = 'W3D'
        self.assertFalse(ani.validate(self))
        self.file_format = 'W3X'
        self.assertFalse(ani.validate(self))

    def test_chunk_sizes(self):
        ani = get_animation_minimal()

        self.assertEqual(44, ani.header.size(False))

        self.assertEqual(43, list_size(ani.channels, False))

        self.assertEqual(95, ani.size(False))
        self.assertEqual(103, ani.size())

        data = [0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0]
        bit_channel = AnimationBitChannel(data=data)
        self.assertEqual(10, bit_channel.size(False))

    def test_write_read_xml(self):
        self.write_read_xml_test(get_animation(xml=True), 'W3DAnimation', Animation.parse, compare_animations, self)

    def test_write_read_minimal_xml(self):
        self.write_read_xml_test(get_animation_minimal(), 'W3DAnimation', Animation.parse, compare_animations, self)

    def test_parse_invalid_identifier(self):
        root = create_root()
        xml_animation = create_node(root, 'W3DAnimation')
        xml_animation.set('id', 'fakeIdentifier')
        xml_animation.set('Hierarchy', 'fakeHiera')
        xml_animation.set('NumFrames', '1')
        xml_animation.set('FrameRate', '22')

        create_node(xml_animation, 'InvalidIdentifier')

        channels = create_node(xml_animation, 'Channels')
        create_node(channels, 'InvalidIdentifier')

        xml_objects = root.findall('W3DAnimation')
        self.assertEqual(1, len(xml_objects))

        with (patch.object(self, 'warning')) as report_func:
            Animation.parse(self, xml_objects[0])

            report_func.assert_has_calls([call('unhandled node \'InvalidIdentifier\' in W3DAnimation!'),
                                          call('unhandled node \'InvalidIdentifier\' in Channels!')])
