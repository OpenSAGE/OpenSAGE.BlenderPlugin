# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os.path

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.export_utils import save
from tests.shared.helpers.hierarchy import *
from tests.shared.helpers.hlod import *
from tests.shared.helpers.mesh import *
from tests.utils import *


class TestExportW3X(TestCase):
    def test_unsupported_export_mode(self):
        export_settings = {}
        export_settings['mode'] = 'NON_EXISTING'

        context = IOWrapper(self.outpath() + 'output_skn', 'W3X')

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

    def test_no_file_created_if_MODE_is_M_and_no_meshes(self):
        export_settings = {}
        export_settings['mode'] = 'M'

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path + extension))

    def test_no_file_created_if_MODE_is_HM_and_no_meshes(self):
        export_settings = {}
        export_settings['mode'] = 'HM'

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path + extension))

    def test_no_file_created_if_MODE_is_HAM_and_no_meshes(self):
        export_settings = {}
        export_settings['mode'] = 'HAM'

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path + extension))

    def test_no_hlod_is_written_if_mode_M(self):
        export_settings = {}
        export_settings['mode'] = 'M'
        export_settings['compression'] = 'U'
        export_settings['create_texture_xmls'] = False

        meshes = [get_mesh()]
        create_data(self, meshes)

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        doc = minidom.parse(file_path + extension)
        assets = doc.getElementsByTagName('AssetDeclaration')

        for node in assets[0].childs():
            self.assertNotEqual('W3DContainer', node.tagName)

    def test_no_hierarchy_is_written_if_mode_M(self):
        export_settings = {}
        export_settings['mode'] = 'M'
        export_settings['create_texture_xmls'] = False
        export_settings['compression'] = 'U'

        meshes = [get_mesh()]
        create_data(self, meshes)

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        doc = minidom.parse(file_path + extension)
        assets = doc.getElementsByTagName('AssetDeclaration')

        for node in assets[0].childs():
            self.assertNotEqual('W3DHierarchy', node.tagName)

    def test_hierarchy_is_written_if_mode_HM_and_not_use_existing_skeleton(self):
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['compression'] = 'U'
        export_settings['create_texture_xmls'] = False
        export_settings['use_existing_skeleton'] = False

        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)

        create_data(self, meshes, hlod, hierarchy)

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        doc = minidom.parse(file_path + extension)
        assets = doc.getElementsByTagName('AssetDeclaration')

        hierarchy_found = False
        for node in assets[0].childs():
            if node.tagName == 'W3DHierarchy':
                hierarchy_found = True

        self.assertTrue(hierarchy_found)

    def test_no_hierarchy_is_written_if_mode_HM_and_use_existing_skeleton(self):
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['compression'] = 'U'
        export_settings['create_texture_xmls'] = False
        export_settings['use_existing_skeleton'] = True

        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)

        create_data(self, meshes, hlod, hierarchy)

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        doc = minidom.parse(file_path + extension)
        assets = doc.getElementsByTagName('AssetDeclaration')

        for node in assets[0].childs():
            self.assertNotEqual('W3DHierarchy', node.tagName)

    def test_no_file_created_if_MODE_is_A_and_U_no_animation_channels(self):
        export_settings = {}
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'U'

        extension = '.w3x'
        file_path = self.outpath() + 'output_ani'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path + extension))

    def test_no_file_created_if_MODE_is_A_and_TC_no_animation_channels(self):
        export_settings = {}
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'TC'

        extension = '.w3x'
        file_path = self.outpath() + 'output_ani'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path + extension))

    def test_no_texture_xml_files_are_created_if_not_create_texture_xmls(self):
        export_settings = {}
        export_settings['create_texture_xmls'] = False
        export_settings['use_existing_skeleton'] = False
        export_settings['mode'] = 'HM'

        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)

        create_data(self, meshes, hlod, hierarchy)

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        self.assertTrue(os.path.exists(file_path + extension))
        self.assertFalse(os.path.exists(self.outpath() + 'texture.xml'))

    def test_texture_xml_files_are_created_if_create_texture_xmls(self):
        export_settings = {}
        export_settings['create_texture_xmls'] = True
        export_settings['use_existing_skeleton'] = False
        export_settings['mode'] = 'HM'

        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)

        create_data(self, meshes, hlod, hierarchy)

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3X')

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        self.assertTrue(os.path.exists(file_path + extension))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))
