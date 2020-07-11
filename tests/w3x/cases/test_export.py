# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os.path
from unittest.mock import patch

from io_mesh_w3d.common.structs.data_context import *
from io_mesh_w3d.w3x.export_w3x import save
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import *
from tests.common.helpers.animation import *
from tests.utils import *


class TestExportW3X(TestCase):
    def test_does_not_apply_extension_if_already_there(self):
        export_settings = {'mode': 'M',
                           'compression': 'U',
                           'individual_files': False,
                           'create_texture_xmls': False}

        data_context = DataContext(
            container_name='containerName',
            meshes=[get_mesh()])

        file_path = self.outpath() + 'output_skn.w3x'
        self.set_format('W3X')
        self.filepath = file_path

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.assertTrue(os.path.exists(self.filepath))
        self.assertFalse(os.path.exists(self.filepath + '.w3x'))

    def test_unsupported_export_mode(self):
        export_settings = {'mode': 'NON_EXISTING'}

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output_skn'

        self.assertEqual({'CANCELLED'}, save(self, export_settings, DataContext()))

    def test_only_mesh_is_written_if_mode_M(self):
        export_settings = {'mode': 'M',
                           'compression': 'U',
                           'individual_files': False,
                           'create_texture_xmls': False}

        data_context = DataContext(
            container_name='containerName',
            meshes=[get_mesh()])

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        self.set_format('W3X')
        self.filepath = file_path

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        root = find_root(self, file_path + extension)
        for child in root:
            self.assertTrue(child.tag in ['W3DMesh', 'Includes'])

    def test_warning_is_shown_if_M_and_multiple_meshes(self):
        export_settings = {'mode': 'M',
                           'compression': 'U'}

        data_context = DataContext(
            container_name='containerName',
            meshes=[get_mesh(), get_mesh()])

        file_path = self.outpath() + 'output_skn'
        self.set_format('W3X')
        self.filepath = file_path

        with (patch.object(self, 'warning')) as warning_func:
            self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

            warning_func.assert_called_with(
                'Scene does contain multiple meshes, exporting only the first with export mode M!')

    def test_hierarchy_is_written_if_mode_HM_and_not_use_existing_skeleton(self):
        export_settings = {'mode': 'HM',
                           'compression': 'U',
                           'individual_files': False,
                           'create_texture_xmls': False,
                           'use_existing_skeleton': False}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        self.set_format('W3X')
        self.filepath = file_path

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        root = find_root(self, file_path + extension)
        self.assertIsNotNone(root.find('W3DHierarchy'))

    def test_no_hierarchy_is_written_if_mode_HM_and_use_existing_skeleton(self):
        export_settings = {'mode': 'HM',
                           'compression': 'U',
                           'individual_files': False,
                           'create_texture_xmls': False,
                           'use_existing_skeleton': True}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        self.set_format('W3X')
        self.filepath = file_path

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        root = find_root(self, file_path + extension)
        self.assertIsNone(root.find('W3DHierarchy'))

    def test_no_texture_xml_files_are_created_if_mode_HM_and_not_create_texture_xmls(self):
        export_settings = {'mode': 'HM',
                           'individual_files': False,
                           'create_texture_xmls': False,
                           'use_existing_skeleton': False}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            textures=['texture.xml'],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        self.set_format('W3X')
        self.filepath = file_path

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.assertTrue(os.path.exists(file_path + extension))
        self.assertFalse(os.path.exists(self.outpath() + 'texture.xml'))

    def test_no_texture_xml_files_are_created_if_mode_HAM_and_not_create_texture_xmls(self):
        export_settings = {'mode': 'HAM',
                           'create_texture_xmls': False}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            textures=['texture.xml'],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name),
            animation=get_animation(hierarchy_name))

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        self.set_format('W3X')
        self.filepath = file_path

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.assertTrue(os.path.exists(file_path + extension))
        self.assertFalse(os.path.exists(self.outpath() + 'texture.xml'))

    def test_texture_xml_files_are_created_if_create_texture_xmls(self):
        export_settings = {'mode': 'HM',
                           'individual_files': False,
                           'create_texture_xmls': True,
                           'use_existing_skeleton': False}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            textures=['texture.xml'],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        extension = '.w3x'
        file_path = self.outpath() + 'output_skn'
        self.set_format('W3X')
        self.filepath = file_path

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.assertTrue(os.path.exists(file_path + extension))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))
