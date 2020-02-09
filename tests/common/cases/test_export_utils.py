# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from unittest.mock import patch
from tests.utils import *
from io_mesh_w3d.export_utils import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.mesh import *


class TestExportUtils(TestCase):
    def test_retrieve_data_returns_false_if_w3d_and_container_name_too_long(self):
        self.error = lambda text: self.assertEqual('Filename is longer than 16 characters, aborting export!', text)

        data_context = DataContext(
            container_name='',
            rig=None,
            meshes=[],
            textures=[],
            collision_boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        export_settings = {}
        export_settings['mode'] = 'M'

        self.filepath = r'C:dir\dir.dir\toolongtestfilename'

        self.assertFalse(retrieve_data(self, export_settings, data_context))

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(None, None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=None)
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value=([], None))
    def test_retrieve_data_returns_false_if_M_in_mode_and_no_meshes(self, retrieve_hierarchy, hlod, boxes, dazzles, retrieve_meshes):
        self.error = lambda text: self.assertEqual('Scene does not contain any meshes, aborting export!', text)

        data_context = DataContext(
            container_name='',
            rig=None,
            meshes=[],
            textures=[],
            collision_boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        export_settings = {}
        export_settings['mode'] = 'M'

        self.filepath = r'C:dir\dir.dir\filename'

        self.assertFalse(retrieve_data(self, export_settings, data_context))

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(None, None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=None)
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value = ([get_mesh(), get_mesh()], None))
    @patch.object(Mesh, 'validate', return_value=False)
    def test_retrieve_data_returns_false_if_M_in_mode_and_invalid_mesh(self, hiera, hlod, boxes, dazzles, retrieve_meshes, validate):
        self.error = lambda text: self.assertEqual('aborting export!', text)

        data_context = DataContext(
            container_name='',
            rig=None,
            meshes=[],
            textures=[],
            collision_boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        export_settings = {}
        export_settings['mode'] = 'M'

        self.filepath = r'C:dir\dir.dir\filename'

        self.assertFalse(retrieve_data(self, export_settings, data_context))
