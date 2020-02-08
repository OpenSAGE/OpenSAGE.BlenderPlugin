# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from unittest.mock import patch
from tests.utils import *
from io_mesh_w3d.export_utils import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.mesh import *
from io_mesh_w3d.common.utils.hierarchy_export import retrieve_hierarchy
from io_mesh_w3d.common.utils.mesh_export import retrieve_meshes


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

    # @patch('io_mesh_w3d.common.utils.hierarchy_export.retrieve_hierarchy', return_value=(get_hierarchy(), None))
    # @patch('io_mesh_w3d.common.utils.mesh_export.retrieve_meshes', return_value=[get_mesh()])
    # def test_retrieve_data_returns_false_if_meshes_are_invalid(self):
    # TODO: find a way to mock function calls
