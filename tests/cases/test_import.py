# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.import_w3d import *
from io_mesh_w3d.io_binary import write_chunk_head
from tests import utils


class TestObjectImport(utils.W3dTestCase):
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