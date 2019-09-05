# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import bpy
from io_mesh_w3d.export_w3d import save
from tests import utils


class TestObjectExport(utils.W3dTestCase):
    def test_export_structure(self):
        # Load a blend file
        self.loadBlend(self.relpath() + "/dol_amroth_citadel/dol_amroth.blend")

        # Load a structure
        export_settings = {}
        export_settings['w3d_mode'] = "M"

        save(self.outpath() + "dol_amroth.w3d", bpy.context, export_settings)

    def test_export_skinned_mesh(self):
        # Load a blend file
        self.loadBlend(self.relpath() + "/elladan/elladan.blend")

        # Load a structure
        export_settings = {}
        export_settings['w3d_mode'] = "M"

        save(self.outpath() + "elladan_skn.w3d", bpy.context, export_settings)

    def test_export_skinned_skeleton(self):
        # Load a blend file
        self.loadBlend(self.relpath() + "/elladan/elladan.blend")

        # Load a structure
        export_settings = {}
        export_settings['w3d_mode'] = "S"

        save(self.outpath() + "elladan_skl.w3d", bpy.context, export_settings)

    def test_export_Aanimation(self):
        # Load a blend file
        self.loadBlend(self.relpath() + "/elladan/elladan_animated.blend")

        # Load a structure
        export_settings = {}
        export_settings['w3d_mode'] = "A"

        save(self.outpath() + "elladan_dieb.w3d", bpy.context, export_settings)
