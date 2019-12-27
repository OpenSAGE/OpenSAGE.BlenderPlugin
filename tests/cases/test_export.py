# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests.utils import TestCase
from io_mesh_w3d.export_w3d import save


class TestExport(TestCase):
    def test_unsupported_export_mode(self):
        export_settings = {}
        export_settings['w3d_mode'] = "B"

        save(self, export_settings)
