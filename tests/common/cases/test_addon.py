# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io_mesh_w3d
from tests.utils import TestCase


class TestAddon(TestCase):
    def test_addon_enabled(self):
        self.assertIsNotNone(io_mesh_w3d.bl_info)
