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

    @patch('io_mesh_w3d.common.utils.hierarchy_export.retrieve_hierarchy')
    @patch('io_mesh_w3d.common.utils.mesh_export.retrieve_meshes')
    def test_retrieve_data_returns_false_if_M_in_mode_and_no_meshes(self, retrieve_hierarchy, retrieve_meshes):
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

    #@patch('io_mesh_w3d.common.utils.hierarchy_export.retrieve_hierarchy')
    @patch("io_mesh_w3d.common.utils.mesh_export.retrieve_meshes", return_value = ([get_mesh(), get_mesh()], None))
    #@patch('io_mesh_w3d.common.structs.mesh.Mesh.validate')
    #@patch.object(T1, 'foo', MagicMock(return_value='patched'))
    def test_retrieve_data_returns_false_if_M_in_mode_and_invalid_mesh(self, retrieve_meshes):
        (meshs, tex) = retrieve_meshes()
        self.assertEqual(2, len(meshs))
        self.assertEqual(None, tex)

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

        print('##############  test')
        self.assertFalse(retrieve_data(self, export_settings, data_context))
