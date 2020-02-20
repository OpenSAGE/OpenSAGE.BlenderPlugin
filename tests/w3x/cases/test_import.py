# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from shutil import copyfile
from unittest.mock import patch

from io_mesh_w3d.w3x.import_w3x import *
from tests.common.helpers.collision_box import get_collision_box
from tests.common.helpers.hierarchy import get_hierarchy
from tests.common.helpers.mesh import get_mesh
from tests.common.helpers.animation import get_animation
from tests.utils import *


class TestObjectImport(TestCase):
    def test_import_animation_only_no_include(self):
        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        animation = get_animation(hierarchy_name)

        # write to file
        write_struct(hierarchy, self.outpath() + hierarchy_name + '.w3x')
        write_struct(animation, self.outpath() + 'animation.w3x')

        # import
        self.set_format('W3X')
        self.filepath = self.outpath() + 'animation.w3x'
        load(self)

        self.assertTrue(hierarchy_name in bpy.data.objects)
        self.assertTrue(hierarchy_name in bpy.data.armatures)

    def test_load_file_file_does_not_exist(self):
        path = self.outpath() + 'output.w3x'
        self.filepath = path
        self.error = lambda text: self.assertEqual(r'file not found: ' + path, text)
        load(self)

    @patch('io_mesh_w3d.w3x.import_w3x.os.path.dirname', return_value='')
    @patch('io_mesh_w3d.w3x.import_w3x.find_root', return_value=None)
    def test_load_file_root_is_none(self, root, dirname):
        path = self.outpath() + 'output.w3x'

        file = open(path, 'w')
        file.write('lorem ipsum')
        file.close()

        self.error = lambda text: self.fail(r'no error should be thrown!')
        load_file(self, None, path)

        dirname.assert_not_called()

    def test_load_file_invalid_node(self):
        path = self.outpath() + 'output.w3x'
        data = '<?xml version=\'1.0\' encoding=\'utf8\'?><AssetDeclaration xmlns="uri:ea.com:eala:asset" ' \
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Invalid></Invalid></AssetDeclaration> '

        file = open(path, 'w')
        file.write(data)
        file.close()

        self.filepath = path
        self.warning = lambda text: self.assertEqual('unsupported node Invalid in file: ' + path, text)
        load(self)

    @patch('io_mesh_w3d.w3x.import_w3x.create_data')
    @patch.object(Mesh, 'container_name', return_value='')
    @patch('io_mesh_w3d.w3x.import_w3x.load_file')
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
        load(self)

        load_file.assert_called()
        mesh.assert_called()
        create.assert_called()