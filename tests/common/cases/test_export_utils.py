# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from unittest.mock import patch
from tests.utils import *
from io_mesh_w3d.export_utils import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.mesh import *
from tests.common.helpers.hlod import *
from tests.common.helpers.collision_box import *


class TestExportUtils(TestCase):
    @patch('io_mesh_w3d.export_utils.retrieve_data', return_value=None)
    def test_cancells_if_not_retrieve_data(self, retrieve):
        self.assertEqual({'CANCELLED'}, save(self, {'mode': 'M'}))

    def test_retrieve_data_returns_false_if_invalid_mode(self):
        self.error = lambda text: self.assertEqual('unsupported export mode: INVALID, aborting export!', text)

        self.assertIsNone(retrieve_data(self, {'mode': 'INVALID'}))

    def test_retrieve_data_returns_false_if_w3d_and_container_name_too_long(self):
        self.error = lambda text: self.assertEqual('Filename is longer than 16 characters, aborting export!', text)

        self.filepath = r'C:dir' + os.path.sep + 'dir.dir' + os.path.sep + 'toolongtestfilename'

        self.assertIsNone(retrieve_data(self, {'mode': 'M'}))

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(None, None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=None)
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value=([], None))
    def test_retrieve_data_returns_false_if_M_in_mode_and_no_meshes(
            self, retrieve_hierarchy, hlod, boxes, dazzles, retrieve_meshes):
        self.error = lambda text: self.assertEqual('Scene does not contain any meshes, aborting export!', text)

        self.filepath = r'C:dir' + os.path.sep + 'dir.dir' + os.path.sep + 'filename'

        self.assertIsNone(retrieve_data(self, {'mode': 'M'}))

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(None, None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=None)
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value=([get_mesh(), get_mesh()], None))
    @patch.object(Mesh, 'validate', return_value=False)
    def test_retrieve_data_returns_false_if_M_in_mode_and_invalid_mesh(
            self, validate, retrieve_meshes, dazzles, boxes, hlod, hiera):
        self.error = lambda text: self.assertEqual('aborting export!', text)

        self.filepath = r'C:dir' + os.path.sep + 'dir.dir' + os.path.sep + 'filename'

        self.assertIsNone(retrieve_data(self, {'mode': 'M'}))
        retrieve_meshes.assert_called()
        validate.assert_called()

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(get_hierarchy(), None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=None)
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value=([get_mesh(), get_mesh()], None))
    @patch.object(Hierarchy, 'validate', return_value=False)
    def test_retrieve_data_returns_false_if_H_in_mode_and_invalid_hierarchy(
            self, hiera, hlod, boxes, dazzles, retrieve_meshes, validate):
        self.error = lambda text: self.assertEqual('aborting export!', text)

        self.filepath = r'C:dir' + os.path.sep + 'dir.dir' + os.path.sep + 'filename'

        self.assertIsNone(retrieve_data(self, {'mode': 'H'}))
        retrieve_meshes.assert_called()
        validate.assert_called()

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(get_hierarchy(), None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=get_hlod())
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value=([get_mesh(), get_mesh()], None))
    @patch.object(Hierarchy, 'validate', return_value=True)
    @patch.object(HLod, 'validate', return_value=False)
    def test_retrieve_data_returns_false_if_mode_is_HM_and_invalid_hlod(
            self, hiera, hlod, boxes, dazzles, retrieve_meshes, h_validate, validate):
        self.error = lambda text: self.assertEqual('aborting export!', text)

        self.filepath = r'C:dir' + os.path.sep + 'dir.dir' + os.path.sep + 'filename'

        self.assertIsNone(retrieve_data(self, {'mode': 'HM'}))
        retrieve_meshes.assert_called()
        h_validate.assert_called()
        validate.assert_called()

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(get_hierarchy(), None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=get_hlod())
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[get_collision_box()])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value=([get_mesh(), get_mesh()], None))
    @patch.object(Hierarchy, 'validate', return_value=True)
    @patch.object(HLod, 'validate', return_value=True)
    @patch.object(CollisionBox, 'validate', return_value=False)
    def test_retrieve_data_returns_false_if_mode_is_HM_and_invalid_box(
            self, hiera, hlod, boxes, dazzles, retrieve_meshes, h_validate, hlod_validate, validate):
        self.error = lambda text: self.assertEqual('aborting export!', text)

        self.filepath = r'C:dir' + os.path.sep + 'dir.dir' + os.path.sep + 'filename'

        self.assertIsNone(retrieve_data(self, {'mode': 'HM'}))
        retrieve_meshes.assert_called()
        h_validate.assert_called()
        hlod_validate.assert_called()
        validate.assert_called()

    @patch('io_mesh_w3d.export_utils.retrieve_hierarchy', return_value=(get_hierarchy(), None))
    @patch('io_mesh_w3d.export_utils.create_hlod', return_value=None)
    @patch('io_mesh_w3d.export_utils.retrieve_boxes', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_dazzles', return_value=[])
    @patch('io_mesh_w3d.export_utils.retrieve_meshes', return_value=([], None))
    @patch.object(Animation, 'validate', return_value=False)
    def test_retrieve_data_returns_false_if_A_in_mode_and_invalid_animation(
            self, hiera, hlod, boxes, dazzles, retrieve_meshes, validate):
        self.error = lambda text: self.assertEqual('aborting export!', text)

        self.filepath = r'C:dir' + os.path.sep + 'dir.dir' + os.path.sep + 'filename'

        self.assertIsNone(retrieve_data(self, {'mode': 'A', 'compression': 'U'}))
        validate.assert_called()
