# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
from io_mesh_w3d.import_w3d import *
from io_mesh_w3d.io_binary import write_chunk_head
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

    def test_unsupported_chunk_skip(self):
        output = open(self.outpath() + "output.w3d", "wb")

        write_chunk_head(output, W3D_CHUNK_MORPH_ANIMATION, 0)
        write_chunk_head(output, W3D_CHUNK_HMODEL, 0)
        write_chunk_head(output, W3D_CHUNK_LODMODEL, 0)
        write_chunk_head(output, W3D_CHUNK_COLLECTION, 0)
        write_chunk_head(output, W3D_CHUNK_POINTS, 0)
        write_chunk_head(output, W3D_CHUNK_LIGHT, 0)
        write_chunk_head(output, W3D_CHUNK_EMITTER, 0)
        write_chunk_head(output, W3D_CHUNK_AGGREGATE, 0)
        write_chunk_head(output, W3D_CHUNK_NULL_OBJECT, 0)
        write_chunk_head(output, W3D_CHUNK_LIGHTSCAPE, 0)
        write_chunk_head(output, W3D_CHUNK_DAZZLE, 0)
        write_chunk_head(output, W3D_CHUNK_SOUNDROBJ, 0)
        output.close()

        sut = utils.ImportWrapper(self.outpath() + "output.w3d")
        load(sut, bpy.context, import_settings={})