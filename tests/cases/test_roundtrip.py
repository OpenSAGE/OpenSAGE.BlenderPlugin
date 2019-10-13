# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import bpy
from io_mesh_w3d.export_w3d import save
from tests import utils


class TestRoundtrip(utils.W3dTestCase):
    def test_roundtrip(self):
        # Load a blend file
        self.loadBlend(self.relpath() + "/dol_amroth_citadel/dol_amroth.blend")
