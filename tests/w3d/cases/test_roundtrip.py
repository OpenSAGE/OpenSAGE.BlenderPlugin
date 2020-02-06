# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from shutil import copyfile

from io_mesh_w3d.export_utils import save
from io_mesh_w3d.w3d.import_w3d import load
from io_mesh_w3d.import_utils import create_data
from tests.common.helpers.animation import get_animation
from tests.common.helpers.collision_box import get_collision_box
from tests.common.helpers.hierarchy import get_hierarchy
from tests.common.helpers.hlod import get_hlod
from tests.common.helpers.mesh import get_mesh
from tests.utils import *
from tests.utils import TestCase, IOWrapper
from tests.w3d.helpers.dazzle import get_dazzle
from tests.w3d.helpers.compressed_animation import get_compressed_animation
from os.path import dirname as up


class TestRoundtripW3D(TestCase):
    def test_roundtrip(self):
        hierarchy_name = 'testhiera_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('testmodelname', hierarchy_name)
        boxes = [get_collision_box()]
        dazzles = [get_dazzle()]
        animation = get_animation(hierarchy_name)

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        context = IOWrapper(self.outpath() + 'output_skn')
        create_data(context, meshes, hlod, hierarchy, boxes, animation, None, dazzles)

        # export
        context = IOWrapper(self.outpath() + 'output_skn', 'W3D')
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['use_existing_skeleton'] = True
        save(context, export_settings)

        context = IOWrapper(self.outpath() + 'testhiera_skl', 'W3D')
        export_settings['mode'] = 'H'
        save(context, export_settings)

        context = IOWrapper(self.outpath() + 'output_ani', 'W3D')
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'U'
        save(context, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(use_empty=True)

        # import
        context = IOWrapper(self.outpath() + 'output_skn.w3d')
        load(context, import_settings={})
        context = IOWrapper(self.outpath() + 'output_ani.w3d')
        load(context, import_settings={})

        # check created objects
        self.assertTrue(hierarchy_name in bpy.data.objects)
        self.assertTrue(hierarchy_name in bpy.data.armatures)
        amt = bpy.data.armatures[hierarchy_name]
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)
        self.assertTrue('Brakelight' in bpy.data.objects)

    def test_roundtrip_compressed_animation(self):
        hierarchy_name = 'testhiera_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod('testmodelname', hierarchy_name)
        boxes = [get_collision_box()]
        dazzles = [get_dazzle()]
        comp_animation = get_compressed_animation(hierarchy_name)

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        context = IOWrapper(self.outpath() + 'output_skn')
        create_data(context, meshes, hlod, hierarchy, boxes, None, comp_animation, dazzles)

        # export
        context = IOWrapper(self.outpath() + 'output_skn', 'W3D')
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['use_existing_skeleton'] = True
        save(context, export_settings)

        context = IOWrapper(self.outpath() + 'testhiera_skl', 'W3D')
        export_settings['mode'] = 'H'
        save(context, export_settings)

        context = IOWrapper(self.outpath() + 'output_comp_ani', 'W3D')
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'TC'
        save(context, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        context = IOWrapper(self.outpath() + 'output_skn.w3d')
        load(context, import_settings={})
        context = IOWrapper(self.outpath() + 'output_comp_ani.w3d')
        load(context, import_settings={})

        # check created objects
        self.assertTrue(hierarchy_name in bpy.data.objects)
        self.assertTrue(hierarchy_name in bpy.data.armatures)
        amt = bpy.data.armatures[hierarchy_name]
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)
        self.assertTrue('Brakelight' in bpy.data.objects)

    def test_roundtrip_HAM(self):
        hierarchy_name = 'TestName'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod(hierarchy_name, hierarchy_name)
        boxes = [get_collision_box()]
        dazzles = [get_dazzle()]
        animation = get_animation(hierarchy_name)

        context = IOWrapper(self.outpath() + 'output')
        create_data(context, meshes, hlod, hierarchy, boxes, animation, None, dazzles)

        # export
        context = IOWrapper(self.outpath() + 'output', 'W3D')
        export_settings = {}
        export_settings['mode'] = 'HAM'
        export_settings['compression'] = 'U'
        save(context, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        context = IOWrapper(self.outpath() + 'output.w3d')
        load(context, import_settings={})

        # check created objects
        self.assertTrue('output' in bpy.data.armatures)
        amt = bpy.data.armatures['output']
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)
        self.assertTrue('Brakelight' in bpy.data.objects)

    def test_roundtrip_HAM_tc_animation(self):
        hierarchy_name = 'TestName'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod(hierarchy_name, hierarchy_name)
        boxes = [get_collision_box()]
        dazzles = [get_dazzle()]
        comp_animation = get_compressed_animation(hierarchy_name)

        context = IOWrapper(self.outpath() + 'output')
        create_data(context, meshes, hlod, hierarchy, boxes, None, comp_animation, dazzles)

        # export
        context = IOWrapper(self.outpath() + 'output', 'W3D')
        export_settings = {}
        export_settings['mode'] = 'HAM'
        export_settings['compression'] = 'TC'
        save(context, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        context = IOWrapper(self.outpath() + 'output.w3d')
        load(context, import_settings={})

        # check created objects
        self.assertTrue('output' in bpy.data.armatures)
        amt = bpy.data.armatures['output']
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)
        self.assertTrue('Brakelight' in bpy.data.objects)

    def test_roundtrip_prelit(self):
        hierarchy_name = 'testhiera_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [get_mesh(name='sword', skin=True, prelit=True),
                  get_mesh(name='soldier', skin=True),
                  get_mesh(name='TRUNK', prelit=True)]
        hlod = get_hlod('TestModelName', hierarchy_name)

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        context = IOWrapper(self.outpath() + 'output')
        create_data(context, meshes, hlod, hierarchy, [], None, None, [])

        # export
        context = IOWrapper(self.outpath() + 'output', 'W3D')
        export_settings = {}
        export_settings['mode'] = 'HM'
        export_settings['use_existing_skeleton'] = False
        save(context, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        context = IOWrapper(self.outpath() + 'output.w3d')
        load(context, import_settings={})

        # check created objects
        self.assertTrue('output' in bpy.data.objects)
        self.assertTrue('output' in bpy.data.armatures)
        amt = bpy.data.armatures['output']
        self.assertEqual(6, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)
