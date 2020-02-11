# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from shutil import copyfile

from io_mesh_w3d.w3d.import_w3d import *
from io_mesh_w3d.w3d.io_binary import *
from tests.common.helpers.collision_box import get_collision_box
from tests.common.helpers.hierarchy import get_hierarchy
from tests.common.helpers.hlod import get_hlod
from tests.common.helpers.mesh import get_mesh
from tests.utils import *
from os.path import dirname as up


class TestImport(TestCase):
    def test_import_no_skeleton_file(self):
        hierarchy_name = 'TestHiera_SKL'
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)
        box = get_collision_box()

        # write to file
        skn = open(self.outpath() + 'base_skn.w3d', 'wb')
        for mesh in meshes:
            mesh.write(skn)
        hlod.write(skn)
        box.write(skn)
        skn.close()

        # import
        self.filepath = self.outpath() + 'base_skn.w3d'
        load(self, import_settings={})

    def test_unsupported_chunk_skip(self):
        output = open(self.outpath() + 'output.w3d', 'wb')

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
        write_chunk_head(W3D_CHUNK_SOUNDROBJ, output, 0)
        output.close()

        self.filepath = self.outpath() + 'output.w3d'
        load(self, import_settings={})

    def test_unkown_chunk_skip(self):
        path = self.outpath() + 'output.w3d'
        file = open(path, 'wb')
        write_chunk_head(0x01, file, 1, has_sub_chunks=False)
        write_ubyte(0x00, file)
        file.close()

        self.warning = lambda text: self.assertEqual('unknown chunk_type in io_stream: 0x1', text)
        load_file(self, None, path)