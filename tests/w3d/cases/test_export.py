# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os.path
from unittest.mock import patch

from io_mesh_w3d.common.structs.data_context import *
from io_mesh_w3d.w3d.export_w3d import save
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import *
from tests.common.helpers.animation import *
from tests.utils import *


class TestExportW3D(TestCase):
    def test_does_not_apply_extension_if_already_there(self):
        export_settings = {'mode': 'M', 'compression': 'U'}

        data_context = DataContext(
            container_name='containerName',
            meshes=[get_mesh()])

        self.filepath = self.outpath() + 'output_skn.w3d'

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.assertTrue(os.path.exists(self.filepath))
        self.assertFalse(os.path.exists(self.filepath + '.w3d'))

    def test_only_mesh_chunk_is_written_if_mode_M(self):
        export_settings = {'mode': 'M', 'compression': 'U'}

        data_context = DataContext(
            container_name='containerName',
            meshes=[get_mesh()])

        self.filepath = self.outpath() + 'output_skn'

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.filepath += '.w3d'
        self.assertTrue(os.path.exists(self.filepath))
        file = open(self.filepath, 'rb')
        filesize = os.path.getsize(self.filepath)

        found_meshes = 0
        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)
            self.assertEqual(W3D_CHUNK_MESH, chunk_type)
            found_meshes += 1
            file.seek(chunk_end, 1)

        file.close()
        self.assertEqual(1, found_meshes)

    def test_warning_is_shown_if_M_and_multiple_meshes(self):
        export_settings = {'mode': 'M', 'compression': 'U'}

        data_context = DataContext(
            container_name='containerName',
            meshes=[get_mesh(), get_mesh()])

        self.filepath = self.outpath() + 'output_skn'

        with (patch.object(self, 'warning')) as warning_func:
            self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

            warning_func.assert_called_with(
                'Scene does contain multiple meshes, exporting only the first with export mode M!')

    def test_error_is_shown_if_unsupported_export_mode(self):
        export_settings = {'mode': 'UNSUPPORTED', 'compression': 'U'}

        data_context = DataContext(
            container_name='containerName',
            meshes=[get_mesh(), get_mesh()])

        self.filepath = self.outpath() + 'output_skn'

        with (patch.object(self, 'error')) as error_func:
            self.assertEqual({'CANCELLED'}, save(self, export_settings, data_context))

            error_func.assert_called_with('unsupported export mode: UNSUPPORTED, aborting export!')

    def test_hierarchy_is_written_if_mode_HM_and_not_use_existing_skeleton(self):
        export_settings = {'mode': 'HM', 'compression': 'U', 'use_existing_skeleton': False}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        self.filepath = self.outpath() + 'output_skn'

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.filepath += '.w3d'
        self.assertTrue(os.path.exists(self.filepath))
        file = open(self.filepath, 'rb')
        filesize = os.path.getsize(self.filepath)

        hierarchy_found = False
        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_HIERARCHY:
                hierarchy_found = True
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

        file.close()
        self.assertTrue(hierarchy_found)

    def test_no_hierarchy_is_written_if_mode_HM_and_use_existing_skeleton(self):
        export_settings = {'mode': 'HM', 'compression': 'U', 'use_existing_skeleton': True}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        self.filepath = self.outpath() + 'output_skn'

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.filepath += '.w3d'
        self.assertTrue(os.path.exists(self.filepath))
        file = open(self.filepath, 'rb')
        filesize = os.path.getsize(self.filepath)

        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

            self.assertNotEqual(W3D_CHUNK_HIERARCHY, chunk_type)
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

        file.close()

    def test_hlod_hierarchy_name_is_container_name_if_export_mode_HM_and_not_use_existing_skeleton(self):
        export_settings = {'mode': 'HM', 'compression': 'U', 'use_existing_skeleton': False}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        self.filepath = self.outpath() + 'output_skn'

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.assertEqual('containerName', data_context.hlod.header.hierarchy_name)

    def test_hierarchy_name_is_container_name_for_hlod_and_animation_if_export_mode_HAM(self):
        export_settings = {'mode': 'HAM', 'compression': 'U', 'use_existing_skeleton': False}

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name),
            animation=get_animation(hierarchy_name))

        self.filepath = self.outpath() + 'output_skn'

        self.assertEqual({'FINISHED'}, save(self, export_settings, data_context))

        self.assertEqual('containerName', data_context.hierarchy.header.name)
        self.assertEqual('containerName', data_context.hlod.header.hierarchy_name)
        self.assertEqual('containerName', data_context.animation.header.hierarchy_name)
