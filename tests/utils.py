# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import inspect
import os
import shutil
import sys
import tempfile
import unittest

import addon_utils
import bpy

from io_mesh_w3d.w3x.io_xml import *


def almost_equal(self, x, y, threshold=0.0001):
    self.assertTrue(abs(x - y) < threshold)

class IOWrapper:
    def __init__(self, filepath, file_format='INVALID'):
        self.filepath = filepath
        self.report = print
        self.file_format = file_format
        if file_format == 'W3D':
            self.filename_ext = '.w3d'
        elif file_format == 'W3X':
            self.filename_ext = '.w3x'

    def info(self, msg):
        pass
        #self.report({'INFO'}, msg)

    def warning(self, msg):
        pass
        #self.report({'WARNING'}, msg)

    def error(self, msg):
        pass
        #self.report({'ERROR'}, msg)


class TestCase(unittest.TestCase):
    __save_test_data = '--save-test-data' in sys.argv
    __tmp_base = os.path.join(tempfile.gettempdir(), 'io_mesh_w3d-tests')
    filepath = os.path.join(__tmp_base, 'out' + os.path.sep)

    firstError = True

    file_format = 'W3D'

    def info(self, msg):
        pass
        #print({'INFO'}, msg)

    def warning(self, msg):
        pass
        # if self.firstError:
        #    print('\n >>>' + self.id() + '<<<')
        #    self.firstError = False
        #print({'WARNING'}, msg)

    def error(self, msg):
        pass
        # if self.firstError:
        #    print('\n' + self.id())
        #    self.firstError = False
        #print({'ERROR'}, msg)

    @classmethod
    def relpath(cls, path=None):
        result = os.path.dirname(inspect.getfile(cls))
        if path is not None:
            result = os.path.join(result, path)
        return result

    @classmethod
    def outpath(cls, path=''):
        if not os.path.exists(cls.filepath):
            os.makedirs(cls.filepath)
        return os.path.join(cls.filepath, path)

    # def loadBlend(self, blend_file):
    #    bpy.ops.wm.open_mainfile(filepath=self.relpath(blend_file))

    def setUp(self):
        bpy.ops.wm.read_homefile(use_empty=True)
        addon_utils.enable('io_mesh_w3d', default_set=True)

    def tearDown(self):
        if os.path.exists(self.filepath):
            if self.__save_test_data:
                bpy.ops.wm.save_mainfile(
                    filepath=os.path.join(self.filepath, 'result.blend'))
                new_path = os.path.join(
                    self.__tmp_base,
                    self.__class__.__name__,
                    self._testMethodName)
                os.renames(self.filepath, new_path)
            else:
                shutil.rmtree(self.filepath)
        addon_utils.disable('io_mesh_w3d')

    def write_read_xml_test(self, expected, identifier, parse, compare, context=None):
        root = create_root()
        expected.create(root)

        # TODO: is this sufficient or should we write to an io.BytesIO ?

        xml_objects = root.findall(identifier)
        self.assertEqual(1, len(xml_objects))

        if context is not None:
            actual = parse(context, xml_objects[0])
        else:
            actual = parse(xml_objects[0])
        compare(self, expected, actual)
