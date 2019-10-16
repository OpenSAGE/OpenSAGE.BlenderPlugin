# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
from io_mesh_w3d.import_w3d import load
from tests import utils


class TestObjectImport(utils.W3dTestCase):
    def test_import_structure(self):
        model = utils.ImportWrapper(
            self.relpath() + "/dol_amroth_citadel/gbdolamr.w3d")

        # Load a structure
        load(model, bpy.context, import_settings={})

        # Check if all meshes exist
        self.assertObjectsExist(["BANNERS", "BLACK", "BUTTRESSES", "CREN01",
                                 "CREN02", "CREN03", "CREN04", "DOME", "ENTRANCE",
                                 "MAIN", "MOAT", "TOP", "WATER", "WHITETREEEMBOSS"])

        # Check if the armature exists
        self.assertObjectsExist(["GBDOLAMRSKL"])

        # TODO: check vertices count etc.

    def test_import_structure_with_bld_ani(self):
        # Load a building animation
        bld_ani = utils.ImportWrapper(
            self.relpath() + "/dol_amroth_citadel/gbdolamr_bld.w3d")

        load(bld_ani, bpy.context, import_settings={})

        # Check if all meshes exist
        self.assertObjectsExist(["BUTTRESSES", "CREN01", "CREN02", "CREN03",
                                 "CREN04", "MAIN", "BLACK", "TOP", "DOME", "ENTRANCE"])
