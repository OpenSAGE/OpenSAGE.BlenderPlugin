# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import inspect
import os
import io
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import addon_utils

from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.w3d.io_binary import *


def almost_equal(self, x, y, threshold=0.0001):
    self.assertTrue(abs(x - y) < threshold)


class TestCase(unittest.TestCase):
    __save_test_data = '--save-test-data' in sys.argv
    __tmp_base = os.path.join(tempfile.gettempdir(), 'io_mesh_w3d-tests')
    __filepath = os.path.join(__tmp_base, 'out' + os.path.sep)

    filepath = ''
    file_format = 'W3D'
    filename_ext = '.w3d'

    def log(con, level, text): return text

    def set_format(self, format):
        self.file_format = format
        if format == 'W3D':
            self.filename_ext = '.w3d'
        else:
            self.filename_ext = '.w3x'

    def enable_logging(self):
        self.log = print

    def info(self, msg):
        self.log({'INFO'}, msg)

    def warning(self, msg):
        self.log({'WARNING'}, msg)

    def error(self, msg):
        self.log({'ERROR'}, msg)

    @classmethod
    def relpath(cls, path=None):
        result = os.path.dirname(inspect.getfile(cls))
        if path is not None:
            result = os.path.join(result, path)
        return result

    @classmethod
    def outpath(cls, path=''):
        if not os.path.exists(cls.__filepath):
            os.makedirs(cls.__filepath)
        return os.path.join(cls.__filepath, path)

    def loadBlend(self, blend_file):
        bpy.ops.wm.open_mainfile(filepath=self.relpath(blend_file))

    @patch('threading.Timer.start')
    def setUp(self, start):
        namespace = self.id().split('.')
        print(namespace[-2] + '.' + namespace[-1])

        self.filepath = self.outpath()
        if not os.path.exists(self.__filepath):
            os.makedirs(self.__filepath)
        bpy.ops.wm.read_homefile(use_empty=True)

        from io_mesh_w3d.__init__ import create_node_groups
        start = create_node_groups()

        addon_utils.enable('io_mesh_w3d', default_set=True)

    def tearDown(self):
        if os.path.exists(self.__filepath):
            if self.__save_test_data:
                bpy.ops.wm.save_mainfile(
                    __filepath=os.path.join(self.__filepath, 'result.blend'))
                new_path = os.path.join(
                    self.__tmp_base,
                    self.__class__.__name__,
                    self._testMethodName)
                os.renames(self.__filepath, new_path)
            else:
                shutil.rmtree(self.__filepath)

        addon_utils.disable('io_mesh_w3d')

    def write_read_test(
            self,
            expected,
            chunk_id,
            read,
            compare,
            context=None,
            pass_end=False,
            adapt=lambda x: x):
        io_stream = io.BytesIO()
        expected.write(io_stream)

        self.assertEqual(expected.size(), io_stream.tell())

        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(chunk_id, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = None
        if context is None:
            if not pass_end:
                actual = read(io_stream)
            else:
                actual = read(io_stream, chunkEnd)
        else:
            if not pass_end:
                actual = read(self, io_stream)
            else:
                actual = read(self, io_stream, chunkEnd)

        adapt(expected)

        compare(self, expected, actual)

    def write_read_xml_test(self, expected, identifier, parse, compare, context=None):
        self.file_format = 'W3X'
        root = create_root()
        expected.create(root)

        # pretty_print(root)
        # print(ET.tostring(root))

        xml_objects = root.findall(identifier)
        self.assertEqual(1, len(xml_objects))

        if context is not None:
            actual = parse(context, xml_objects[0])
        else:
            actual = parse(xml_objects[0])
        compare(self, expected, actual)
