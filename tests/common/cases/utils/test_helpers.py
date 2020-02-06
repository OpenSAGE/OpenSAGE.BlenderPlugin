# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import os
from shutil import copyfile
from os.path import dirname as up

from io_mesh_w3d.common.utils.helpers import *


class TestHelpers(TestCase):
    def test_texture_file_extensions(self):
        extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']

        self.warning = lambda text: self.fail(text)

        for extension in extensions:
            copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                     self.outpath() + 'texture' + extension)

            find_texture(self, 'texture')

            # reset scene
            bpy.ops.wm.read_homefile(use_empty=True)
            os.remove(self.outpath() + 'texture' + extension)

    def test_invalid_texture_file_extension(self):
        extensions = ['.invalid']

        self.info = lambda text: self.fail(text)

        for extension in extensions:
            copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                     self.outpath() + 'texture' + extension)

            find_texture(self, 'texture')

            # reset scene
            bpy.ops.wm.read_homefile(use_empty=True)
            os.remove(self.outpath() + 'texture' + extension)