# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.import_w3d import *
from tests.common.helpers.collision_box import get_collision_box
from tests.common.helpers.hlod import get_hlod
from tests.common.helpers.mesh import get_mesh
from tests.common.helpers.hierarchy import get_hierarchy
from tests.common.helpers.animation import get_animation
from tests.w3d.helpers.compressed_animation import get_compressed_animation
from tests.utils import *
from unittest.mock import patch, call


class TestImport(TestCase):
    def test_import_no_skeleton_file_found(self):
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
        load(self)

    def test_skips_multiple_hlod_chunks(self):
        hlod = get_hlod()
        skn = open(self.outpath() + 'output.w3d', 'wb')

        hlod.write(skn)
        hlod.write(skn)
        skn.close()

        # import
        with (patch.object(self, 'warning')) as warning_func:
            self.filepath = self.outpath() + 'output.w3d'
            load(self)
            warning_func.assert_called_with('-> already got one hlod chunk (skipping this one)!')

    def test_skips_multiple_hierarchy_chunks(self):
        hierarchy = get_hierarchy()
        skl = open(self.outpath() + 'output.w3d', 'wb')

        hierarchy.write(skl)
        hierarchy.write(skl)
        skl.close()

        # import
        with (patch.object(self, 'warning')) as warning_func:
            self.filepath = self.outpath() + 'output.w3d'
            self.assertEqual({'FINISHED'}, load(self))
            warning_func.assert_called_with('-> already got one hierarchy chunk (skipping this one)!')

    def test_skips_multiple_animation_chunks(self):
        animation = get_animation()
        comp_animation = get_compressed_animation()
        ani = open(self.outpath() + 'output.w3d', 'wb')

        animation.write(ani)
        animation.write(ani)
        comp_animation.write(ani)
        ani.close()

        # import
        with (patch.object(self, 'warning')) as warning_func:
            self.filepath = self.outpath() + 'output.w3d'
            load(self)

            msg = '-> already got one animation chunk (skipping this one)!'
            warning_func.assert_has_calls([call(msg), call(msg)])

    def test_skips_multiple_compressed_animation_chunks(self):
        animation = get_animation()
        comp_animation = get_compressed_animation()
        ani = open(self.outpath() + 'output.w3d', 'wb')

        comp_animation.write(ani)
        animation.write(ani)
        animation.write(ani)
        ani.close()

        # import
        with (patch.object(self, 'warning')) as warning_func:
            self.filepath = self.outpath() + 'output.w3d'
            load(self)

            msg = '-> already got one animation chunk (skipping this one)!'
            warning_func.assert_has_calls([call(msg), call(msg)])

    def test_animation_import_no_skeleton_file_found(self):
        hierarchy_name = 'TestHiera_SKL'
        animation = get_animation(hierarchy_name)

        # write to file
        ani = open(self.outpath() + 'animation.w3d', 'wb')
        animation.write(ani)
        ani.close()

        # import
        self.filepath = self.outpath() + 'animation.w3d'
        load(self)

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
        load(self)

    def test_unkown_chunk_skip(self):
        path = self.outpath() + 'output.w3d'
        file = open(path, 'wb')
        write_chunk_head(0x01, file, 1, has_sub_chunks=False)
        write_ubyte(0x00, file)
        file.close()

        self.warning = lambda text: self.assertEqual('unknown chunk_type in io_stream: 0x1', text)
        load_file(self, None, path)