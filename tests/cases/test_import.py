# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
from io_mesh_w3d.import_w3d import load
from tests import utils


class ImportWrapper:
    def __init__(self, filepath):
        self.filepath = filepath


class TestObjectImport(utils.W3dTestCase):
    def test_import_structure(self):
        model = ImportWrapper(
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
        bld_ani = ImportWrapper(
            self.relpath() + "/dol_amroth_citadel/gbdolamr_bld.w3d")

        load(bld_ani, bpy.context, import_settings={})

        # Check if all meshes exist
        self.assertObjectsExist(["BUTTRESSES", "CREN01", "CREN02", "CREN03",
                                 "CREN04", "MAIN", "BLACK", "TOP", "DOME", "ENTRANCE"])

    def test_import_skinned_animated_model(self):
        model = ImportWrapper(
            self.relpath() + "/elladan/auelladan.w3d")

        # Load a hero unit
        load(model, bpy.context, import_settings={})

        expected_objects = ["BODY", "BOUNDINGBOX", "BROOCH", "CLOAK", "ELLADANHAIR",
                            "HEAD", "LEGS", "SHEATH", "SWORDELLA", "AUELLADAN_SKL"]

        self.assertIsNotNone(bpy.data.collections["AUELLADAN"])
        collection = bpy.data.collections["AUELLADAN"]
        self.assertEqual(10, len(collection.objects))

        self.assertObjectsExist(expected_objects)

        # Load an attack animation
        atk_ani = ImportWrapper(
            self.relpath() + "/elladan/auelladan_atnf.w3d")

        load(atk_ani, bpy.context, import_settings={})

    def test_import_skinned_animated_model_uncompressed(self):
        model = ImportWrapper(
            self.relpath() + "/elladan/auelladan.w3d")

        # Load a hero unit
        load(model, bpy.context, import_settings={})

        expected_objects = ["BODY", "BOUNDINGBOX", "BROOCH", "CLOAK", "ELLADANHAIR",
                            "HEAD", "LEGS", "SHEATH", "SWORDELLA", "AUELLADAN_SKL"]

        self.assertIsNotNone(bpy.data.collections["AUELLADAN"])
        collection = bpy.data.collections["AUELLADAN"]
        self.assertEqual(10, len(collection.objects))

        self.assertObjectsExist(expected_objects)

        # Load an attack animation
        atk_ani = ImportWrapper(
            self.relpath() + "/elladan/auelladan_diea.w3d")

        load(atk_ani, bpy.context, import_settings={})

    def test_import_skinned_animated_model_compressed(self):
        model = ImportWrapper(
            self.relpath() + "/elladan/auelladan.w3d")

        # Load a hero unit
        load(model, bpy.context, import_settings={})

        expected_objects = ["BODY", "BOUNDINGBOX", "BROOCH", "CLOAK", "ELLADANHAIR",
                            "HEAD", "LEGS", "SHEATH", "SWORDELLA", "AUELLADAN_SKL"]

        self.assertIsNotNone(bpy.data.collections["AUELLADAN"])
        collection = bpy.data.collections["AUELLADAN"]
        self.assertEqual(10, len(collection.objects))

        self.assertObjectsExist(expected_objects)

        # Load an attack animation
        atk_ani = ImportWrapper(
            self.relpath() + "/elladan/auelladan_dieb.w3d")

        load(atk_ani, bpy.context, import_settings={})
