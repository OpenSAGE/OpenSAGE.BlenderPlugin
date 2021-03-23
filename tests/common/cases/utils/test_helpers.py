# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests.utils import TestCase
from shutil import copyfile
from os.path import dirname as up
from io_mesh_w3d.common.utils.helpers import *
from unittest.mock import patch, call


class FakeClass:
    def __init__(self):
        self.tx_coords = []
        self.tx_stages = []


class TestHelpers(TestCase):
    def test_texture_file_extensions(self):
        extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']

        with (patch.object(self, 'info')) as report_func:
            for extension in extensions:
                copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                         self.outpath() + 'texture' + extension)

                find_texture(self, 'texture')

                # reset scene
                bpy.ops.wm.read_homefile(use_empty=True)
                os.remove(self.outpath() + 'texture' + extension)

                report_func.assert_called()

    def test_texture_file_extensions_is_dds_if_file_is_dds_but_tga_referenced(self):
        with (patch.object(self, 'info')) as report_func:
            for extension in extensions:
                copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                         self.outpath() + 'texture.dds')

                find_texture(self, 'texture', 'texture.tga')

                # reset scene
                bpy.ops.wm.read_homefile(use_empty=True)
                os.remove(self.outpath() + 'texture.dds')

                report_func.assert_called_with(f'loaded texture: {self.outpath()}texture.dds')

    def test_texture_file_extensions_is_tga_if_file_is_tga_but_dds_referenced(self):
        with (patch.object(self, 'info')) as report_func:
            for extension in extensions:
                copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                         self.outpath() + 'texture.tga')

                find_texture(self, 'texture', 'texture.dds')

                # reset scene
                bpy.ops.wm.read_homefile(use_empty=True)
                os.remove(self.outpath() + 'texture.tga')

                report_func.assert_called_with(f'loaded texture: {self.outpath()}texture.tga')

    def test_invalid_texture_file_extension(self):
        extensions = ['.invalid']

        with (patch.object(self, 'warning')) as report_func:
            for extension in extensions:
                copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                         self.outpath() + 'texture' + extension)

                find_texture(self, 'texture')

                # reset scene
                bpy.ops.wm.read_homefile(use_empty=True)
                os.remove(self.outpath() + 'texture' + extension)

                report_func.assert_called()

    def test_call_create_uv_layer_without_tx_coords(self):
        fake_mat_pass = FakeClass()

        create_uvlayer(self, None, None, None, fake_mat_pass)
