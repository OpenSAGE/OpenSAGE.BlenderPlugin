# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from shutil import copyfile

from io_mesh_w3d.export_utils import save
from io_mesh_w3d.w3x.import_w3x import load
from io_mesh_w3d.import_utils import create_data
from tests.common.helpers.animation import get_animation
from tests.common.helpers.collision_box import get_collision_box
from tests.common.helpers.hierarchy import get_hierarchy
from tests.common.helpers.hlod import get_hlod
from tests.common.helpers.mesh import get_mesh
from tests.utils import *
from tests.utils import TestCase
from os.path import dirname as up


class TestRoundtripW3X(TestCase):
    def test_roundtrip(self):
        hierarchy_name = 'testhiera_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)
        boxes = [get_collision_box()]
        animation = get_animation(hierarchy_name, xml=True)

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        self.filepath = self.outpath() + 'output_skn'
        create_data(self, meshes, hlod, hierarchy, boxes, animation, None)

        self.set_format('W3X')

        # export
        self.filepath = self.outpath() + 'output_skn'
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['individual_files'] = False
        export_settings['use_existing_skeleton'] = True
        export_settings['create_texture_xmls'] = True
        save(self, export_settings)

        self.filepath = self.outpath() + 'testhiera_skl'
        export_settings['mode'] = 'H'
        save(self, export_settings)

        self.filepath = self.outpath() + 'output_ani'
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'U'
        save(self, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output_skn.w3x'
        load(self, import_settings={})
        self.filepath = self.outpath() + 'output_ani.w3x'
        load(self, import_settings={})

        # check created objects
        self.assertTrue(hierarchy_name in bpy.data.objects)
        self.assertTrue(hierarchy_name in bpy.data.armatures)
        amt = bpy.data.armatures[hierarchy_name]
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

    def test_roundtrip_HAM(self):
        hierarchy_name = 'testname'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod(hierarchy_name, hierarchy_name)
        boxes = [get_collision_box()]
        animation = get_animation(hierarchy_name, xml=True)

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output'
        create_data(self, meshes, hlod, hierarchy, boxes, animation, None)

        # export
        self.filepath = self.outpath() + 'output'
        export_settings = {}
        export_settings['mode'] = 'HAM'
        export_settings['compression'] = 'U'
        export_settings['individual_files'] = False
        export_settings['create_texture_xmls'] = True
        save(self, export_settings)

        # check created files
        self.assertTrue(os.path.exists(self.outpath() + 'output.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output.w3x'
        load(self, import_settings={})

        # check created objects
        self.assertTrue('output' in bpy.data.objects)
        self.assertTrue('output' in bpy.data.armatures)
        amt = bpy.data.armatures['output']
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

    def test_roundtrip_splitted(self):
        hierarchy_name = 'testname_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod(hierarchy_name, hierarchy_name)
        boxes = [get_collision_box()]
        animation = get_animation(hierarchy_name, xml=True)

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output_skn'
        create_data(self, meshes, hlod, hierarchy, boxes, animation, None)

        # export
        self.filepath = self.outpath() + 'output_skn'
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['compression'] = 'U'
        export_settings['individual_files'] = True
        export_settings['create_texture_xmls'] = True
        export_settings['use_existing_skeleton'] = True
        save(self, export_settings)

        # check created files
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.sword.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.soldier.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.TRUNK.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.BOUNDINGBOX.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'testname_skl.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output_skn.w3x'
        load(self, import_settings={})

        # check created objects
        self.assertTrue('testname_skl' in bpy.data.objects)
        self.assertTrue('testname_skl' in bpy.data.armatures)
        amt = bpy.data.armatures['testname_skl']
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

    def test_roundtrip_single_mesh_imports(self):
        hierarchy_name = 'testname_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod(hierarchy_name, hierarchy_name)
        boxes = [get_collision_box()]
        animation = get_animation(hierarchy_name, xml=True)

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output_skn'
        create_data(self, meshes, hlod, hierarchy, boxes, animation, None)

        # export
        self.filepath = self.outpath() + 'output_skn'
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['compression'] = 'U'
        export_settings['individual_files'] = True
        export_settings['create_texture_xmls'] = True
        export_settings['use_existing_skeleton'] = True
        save(self, export_settings)

        # check created files
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.sword.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.soldier.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.TRUNK.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.BOUNDINGBOX.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'testname_skl.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output_skn.TRUNK.w3x'
        load(self, import_settings={})

        # check created objects
        self.assertEqual(2, len(bpy.data.collections))

        self.assertTrue('testname_skl' in bpy.data.objects)
        self.assertTrue('testname_skl' in bpy.data.armatures)
        amt = bpy.data.armatures['testname_skl']
        self.assertEqual(6, len(amt.bones))

        self.assertFalse('sword' in bpy.data.objects)
        self.assertFalse('soldier' in bpy.data.objects)
        self.assertFalse('BOUNDINGBOX' in bpy.data.objects)

        self.assertTrue('TRUNK' in bpy.data.objects)

        # import
        self.filepath = self.outpath() + 'output_skn.sword.w3x'
        load(self, import_settings={})

        self.assertEqual(2, len(bpy.data.collections))

        self.assertFalse('soldier' in bpy.data.objects)
        self.assertFalse('BOUNDINGBOX' in bpy.data.objects)

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

        # import
        self.filepath = self.outpath() + 'output_skn.BOUNDINGBOX.w3x'
        load(self, import_settings={})

        self.assertEqual(2, len(bpy.data.collections))

        self.assertFalse('soldier' in bpy.data.objects)

        self.assertTrue('BOUNDINGBOX' in bpy.data.objects)
        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)
