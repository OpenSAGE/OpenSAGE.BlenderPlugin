# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os.path

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.w3d.export_w3d import save
from tests.shared.helpers.hierarchy import *
from tests.shared.helpers.hlod import *
from tests.shared.helpers.mesh import *
from tests.utils import *


class TestExport(TestCase):
    def test_unsupported_export_mode(self):
        export_settings = {}
        export_settings['mode'] = 'NON_EXISTING'

        self.assertEqual({'CANCELLED'}, save(self, export_settings))

    def test_no_file_created_if_MODE_is_M_and_no_meshes(self):
        export_settings = {}
        export_settings['mode'] = 'M'

        file_path = self.outpath() + 'output_skn.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path))

    def test_no_file_created_if_MODE_is_HM_and_no_meshes(self):
        export_settings = {}
        export_settings['mode'] = 'HM'

        file_path = self.outpath() + 'output_skn.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path))

    def test_no_file_created_if_MODE_is_HAM_and_no_meshes(self):
        export_settings = {}
        export_settings['mode'] = 'HAM'

        file_path = self.outpath() + 'output_skn.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path))

    def test_no_hlod_is_written_if_mode_M(self):
        export_settings = {}
        export_settings['mode'] = 'M'
        export_settings['compression'] = 'U'

        meshes = [get_mesh()]
        create_data(self, meshes)

        file_path = self.outpath() + 'output_skn.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        file = open(file_path, 'rb')
        filesize = os.path.getsize(file_path)
        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

            self.assertNotEqual(W3D_CHUNK_HLOD, chunk_type)
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

        file.close()

    def test_no_hierarchy_is_written_if_mode_M(self):
        export_settings = {}
        export_settings['mode'] = 'M'
        export_settings['compression'] = 'U'

        meshes = [get_mesh()]
        create_data(self, meshes)

        file_path = self.outpath() + 'output_skn.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        file = open(file_path, 'rb')
        filesize = os.path.getsize(file_path)
        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

            self.assertNotEqual(W3D_CHUNK_HIERARCHY, chunk_type)
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

        file.close()

    def test_hierarchy_is_written_if_mode_HM_and_not_use_existing_skeleton(self):
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['compression'] = 'U'
        export_settings['use_existing_skeleton'] = False

        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)

        create_data(self, meshes, hlod, hierarchy)

        file_path = self.outpath() + 'output_skn.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'FINISHED'}, save(context, export_settings))

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
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)

        create_data(self, meshes, hlod, hierarchy)

        file_path = self.outpath() + 'output_skn.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'FINISHED'}, save(context, export_settings))

        file = open(file_path, 'rb')
        filesize = os.path.getsize(file_path)
        while file.tell() < filesize:
            (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

            self.assertNotEqual(W3D_CHUNK_HIERARCHY, chunk_type)
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

        file.close()

    def test_no_file_created_if_MODE_is_A_and_U_no_animation_channels(self):
        export_settings = {}
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'U'

        file_path = self.outpath() + 'output_ani.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path))

    def test_no_file_created_if_MODE_is_A_and_TC_no_animation_channels(self):
        export_settings = {}
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'TC'

        file_path = self.outpath() + 'output_ani.w3d'
        context = IOWrapper(file_path)

        self.assertEqual({'CANCELLED'}, save(context, export_settings))

        self.assertFalse(os.path.exists(file_path))
