# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from shutil import copyfile
from unittest.mock import patch

from io_mesh_w3d.w3x.import_w3x import *
from io_mesh_w3d.w3x.io_xml import *
from tests.common.helpers.collision_box import get_collision_box
from tests.common.helpers.hierarchy import get_hierarchy
from tests.common.helpers.hlod import get_hlod
from tests.common.helpers.mesh import get_mesh
from tests.common.helpers.animation import get_animation
from tests.utils import *
from os.path import dirname as up


class TestObjectImport(TestCase):
    def test_import_animation_only_no_include(self):
        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        animation = get_animation(hierarchy_name)

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        # write to file
        write_struct(hierarchy, self.outpath() + hierarchy_name + '.w3x')
        write_struct(animation, self.outpath() + 'animation.w3x')

        # import
        self.set_format('W3X')
        self.filepath = self.outpath() + 'animation.w3x'
        load(self, import_settings={})

        self.assertTrue(hierarchy_name in bpy.data.objects)
        self.assertTrue(hierarchy_name in bpy.data.armatures)

    def test_load_file_file_does_not_exist(self):
        path = self.outpath() + 'output.w3x'
        self.filepath = path
        self.error = lambda text: self.assertEqual(r'file not found: ' + path, text)
        load(self, import_settings={})

    @patch('io_mesh_w3d.w3x.import_w3x.find_root', return_value=None)
    def test_load_file_root_is_none(self, root):
        self.filepath = self.outpath() + 'output.w3x'
        load(self, import_settings={})

    def test_load_file_invalid_node(self):
        path = self.outpath() + 'output.w3x'
        data = '<?xml version=\'1.0\' encoding=\'utf8\'?><AssetDeclaration xmlns="uri:ea.com:eala:asset" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Invalid></Invalid></AssetDeclaration>'

        file = open(path, 'w')
        file.write(data)
        file.close()

        self.filepath = path
        self.warning = lambda text: self.assertEqual('unsupported node Invalid in file: ' + path, text)
        load(self, import_settings={})

    @patch('io_mesh_w3d.w3x.import_w3x.load_file')
    @patch.object(Mesh, 'container_name', return_value='')
    @patch('io_mesh_w3d.w3x.import_w3x.create_data')
    def test_mesh_only_import(self, load_file, mesh, create):
        data_context = DataContext(
            container_name='',
            rig=None,
            meshes=[get_mesh()],
            textures=[],
            collision_boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        load_file.return_value = data_context

        self.filepath = self.outpath() + 'output.w3x'
        load(self, import_settings={})

        create.assert_called()

    @patch('io_mesh_w3d.w3x.import_w3x.load_file')
    @patch.object(CollisionBox, 'container_name', return_value='')
    @patch('io_mesh_w3d.w3x.import_w3x.create_data')
    def test_mesh_only_import(self, load_file, mesh, create):
        data_context = DataContext(
            container_name='',
            rig=None,
            meshes=[],
            textures=[],
            collision_boxes=[get_collision_box()],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        load_file.return_value = data_context

        self.filepath = self.outpath() + 'output.w3x'
        load(self, import_settings={})

        create.assert_called()