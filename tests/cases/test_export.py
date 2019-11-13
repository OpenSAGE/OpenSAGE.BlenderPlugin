# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.export_w3d import save
from tests import utils


class TestExport(utils.W3dTestCase):
    def test_unsupported_export_mode(self):
        context = utils.ImportWrapper(self.outpath() + "output_skn.w3d")
        export_settings = {}
        export_settings['w3d_mode'] = "B"

        save(context, bpy.context, export_settings)
