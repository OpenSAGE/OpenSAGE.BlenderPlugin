# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests.utils import TestCase
from shutil import copyfile
from os.path import dirname as up
from io_mesh_w3d.common.utils.helpers import *


class FakeClass:
    def __init__(self):
        self.tx_coords = []
        self.tx_stages = []


class TestHelpers(TestCase):
    def test_texture_file_extensions(self):
        extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']

        self.warning = lambda text: self.fail(text)

        for extension in extensions:
            copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                     self.outpath() + 'texture' + extension)

            find_texture(self, 'texture')

            # reset scene
            bpy.ops.wm.read_homefile(use_empty=True)
            os.remove(self.outpath() + 'texture' + extension)

    def test_invalid_texture_file_extension(self):
        extensions = ['.invalid']

        self.info = lambda text: self.fail(text)

        for extension in extensions:
            copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                     self.outpath() + 'texture' + extension)

            find_texture(self, 'texture')

            # reset scene
            bpy.ops.wm.read_homefile(use_empty=True)
            os.remove(self.outpath() + 'texture' + extension)

    def test_call_create_uv_layer_without_tx_coords(self):
        fake_mat_pass = FakeClass()

        create_uvlayer(self, None, None, None, fake_mat_pass)
