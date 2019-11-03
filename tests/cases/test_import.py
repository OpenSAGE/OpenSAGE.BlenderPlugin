# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.import_w3d import *
from io_mesh_w3d.io_binary import write_chunk_head
from tests import utils


class TestObjectImport(utils.W3dTestCase):
    def test_unsupported_chunk_skip(self):
        output = open(self.outpath() + "output.w3d", "wb")

        write_chunk_head(W3D_CHUNK_MORPH_ANIMATION, output, 0)
        write_chunk_head(W3D_CHUNK_HMODEL, output, 0)
        write_chunk_head(W3D_CHUNK_LODMODEL, output, 0)
        write_chunk_head(W3D_CHUNK_COLLECTION, output, 0)
        write_chunk_head(W3D_CHUNK_POINTS, output, 0)
        write_chunk_head(W3D_CHUNK_LIGHT, output, 0)
        write_chunk_head(W3D_CHUNK_EMITTER, output, 0)
        write_chunk_head(W3D_CHUNK_AGGREGATE, output, 0)
        write_chunk_head(W3D_CHUNK_NULL_OBJECT, output, 0)
        write_chunk_head(W3D_CHUNK_LIGHTSCAPE, output, 0)
        write_chunk_head(W3D_CHUNK_DAZZLE, output, 0)
        write_chunk_head(W3D_CHUNK_SOUNDROBJ, output, 0)
        output.close()

        sut = utils.ImportWrapper(self.outpath() + "output.w3d")
        load(sut, bpy.context, import_settings={})