# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os.path
from unittest.mock import patch

from io_mesh_w3d.common.structs.data_context import *
from io_mesh_w3d.import_utils import *
from io_mesh_w3d.w3d.export_w3d import save
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import *
from tests.utils import *


class TestExportW3D(TestCase):
    def test_only_mesh_chunk_is_written_if_mode_M(self):
        export_settings = {}
        export_settings['mode'] = 'M'
        export_settings['compression'] = 'U'

        data_context = DataContext(
            container_name='containerName',
            rig=None,
            meshes=[get_mesh()],
            textures=[],
            boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3D')

        self.assertEqual({'FINISHED'}, save(context, export_settings, data_context))

        file_path += '.w3d'
        self.assertTrue(os.path.exists(file_path))
        file = open(file_path, 'rb')
        filesize = os.path.getsize(file_path)

        found_meshes = 0
        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)
            self.assertEqual(W3D_CHUNK_MESH, chunk_type)
            found_meshes += 1
            file.seek(chunk_end, 1)

        file.close()
        self.assertEqual(1, found_meshes)

    def test_warning_is_shown_if_M_and_multiple_meshes(self):
        export_settings = {}
        export_settings['mode'] = 'M'
        export_settings['compression'] = 'U'

        data_context = DataContext(
            container_name='containerName',
            rig=None,
            meshes=[get_mesh(), get_mesh()],
            textures=[],
            boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3D')

        with (patch.object(IOWrapper, 'warning')) as warning_func:
            self.assertEqual({'FINISHED'}, save(context, export_settings, data_context))

            warning_func.assert_called_with(
                'Scene does contain multiple meshes, exporting only the first with export mode M!')

    def test_error_is_shown_if_unsupported_export_mode(self):
        export_settings = {}
        export_settings['mode'] = 'UNSUPPORTED'
        export_settings['compression'] = 'U'

        data_context = DataContext(
            container_name='containerName',
            rig=None,
            meshes=[get_mesh(), get_mesh()],
            textures=[],
            boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3D')

        with (patch.object(IOWrapper, 'error')) as error_func:
            self.assertEqual({'CANCELLED'}, save(context, export_settings, data_context))

            error_func.assert_called_with('unsupported export mode: UNSUPPORTED, aborting export!')

    def test_hierarchy_is_written_if_mode_HM_and_not_use_existing_skeleton(self):
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['compression'] = 'U'
        export_settings['use_existing_skeleton'] = False

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            rig=None,
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            textures=[],
            boxes=[],
            dazzles=[],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3D')

        self.assertEqual({'FINISHED'}, save(context, export_settings, data_context))

        file_path += '.w3d'
        self.assertTrue(os.path.exists(file_path))
        file = open(file_path, 'rb')
        filesize = os.path.getsize(file_path)

        hierarchy_found = False
        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_HIERARCHY:
                hierarchy_found = True
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

        file.close()
        self.assertTrue(hierarchy_found)

    def test_no_hierarchy_is_written_if_mode_HM_and_use_existing_skeleton(self):
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['compression'] = 'U'
        export_settings['use_existing_skeleton'] = True

        hierarchy_name = 'TestHiera_SKL'

        data_context = DataContext(
            container_name='containerName',
            rig=None,
            meshes=[
                get_mesh(name='sword', skin=True),
                get_mesh(name='soldier', skin=True),
                get_mesh(name='TRUNK')],
            textures=[],
            boxes=[],
            dazzles=[],
            hierarchy=get_hierarchy(hierarchy_name),
            hlod=get_hlod('TestModelName', hierarchy_name))

        file_path = self.outpath() + 'output_skn'
        context = IOWrapper(file_path, 'W3D')

        self.assertEqual({'FINISHED'}, save(context, export_settings, data_context))

        file_path += '.w3d'
        self.assertTrue(os.path.exists(file_path))
        file = open(file_path, 'rb')
        filesize = os.path.getsize(file_path)

        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

            self.assertNotEqual(W3D_CHUNK_HIERARCHY, chunk_type)
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

        file.close()
