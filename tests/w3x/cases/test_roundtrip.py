# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.common.structs.mesh import *
from io_mesh_w3d.export_utils import save_data
from io_mesh_w3d.w3x.import_w3x import load
from io_mesh_w3d.import_utils import create_data
from io_mesh_w3d.common.utils.mesh_import import *
from tests.common.helpers.animation import get_animation
from tests.common.helpers.collision_box import get_collision_box
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import get_mesh
from tests.common.helpers.mesh_structs.texture import get_texture
from tests.utils import *
from tests.utils import TestCase


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

        self.filepath = self.outpath() + 'output_skn'
        create_data(self, meshes, hlod, hierarchy, boxes, animation, None)

        self.set_format('W3X')

        # export
        self.filepath = self.outpath() + 'output_skn'
        export_settings = {'mode': 'HM', 'individual_files': False, 'use_existing_skeleton': True,
                           'create_texture_xmls': True}
        save_data(self, export_settings)

        self.filepath = self.outpath() + 'testhiera_skl'
        export_settings['mode'] = 'H'
        save_data(self, export_settings)

        self.filepath = self.outpath() + 'output_ani'
        export_settings['mode'] = 'A'
        export_settings['compression'] = 'U'
        export_settings['compression_bits'] = 4
        save_data(self, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output_skn.w3x'
        load(self)
        self.filepath = self.outpath() + 'output_ani.w3x'
        load(self)

        # check created objects
        self.assertTrue(hierarchy_name.upper() in bpy.data.objects)
        self.assertTrue(hierarchy_name.upper() in bpy.data.armatures)
        amt = bpy.data.armatures[hierarchy_name.upper()]
        self.assertEqual(7, len(amt.bones))

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
        export_settings = {'mode': 'HAM', 'compression': 'U', 'compression_bits': 4, 'individual_files': False, 'create_texture_xmls': True}
        save_data(self, export_settings)

        # check created files
        self.assertTrue(os.path.exists(self.outpath() + 'output.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output.w3x'
        load(self)

        # check created objects
        self.assertTrue('testname' in bpy.data.objects)
        self.assertTrue('testname' in bpy.data.armatures)
        amt = bpy.data.armatures['testname']
        self.assertEqual(7, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

    def test_roundtrip_texture_name_with_dots(self):
        hierarchy_name = 'testname_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        mesh = get_mesh(name='sword', skin=True)
        mesh.textures = [get_texture(name='tex.with.dots.in.name.but.not.used.dds'),
                         get_texture(name='another.tex.with.dots.in.name.dds')]
        meshes = [mesh]
        hlod = get_hlod(hierarchy_name, hierarchy_name)

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output_skn'
        create_data(self, meshes, hlod, hierarchy)

        # export
        self.filepath = self.outpath() + 'output_skn'
        export_settings = {'mode': 'HM', 'compression': 'U', 'individual_files': True, 'create_texture_xmls': True,
                           'use_existing_skeleton': True}
        save_data(self, export_settings)

        # check created files
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.sword.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'another.tex.with.dots.in.name.xml'))

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output_skn.w3x'
        load(self)

        self.assertTrue('sword' in bpy.data.objects)

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
        export_settings = {'mode': 'HM', 'compression': 'U', 'individual_files': True, 'create_texture_xmls': True,
                           'use_existing_skeleton': False}
        save_data(self, export_settings)

        # check created files
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.sword.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.soldier.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.TRUNK.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output_skn.BOUNDINGBOX.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'testname_skl.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))

        # check created include entries
        root = find_root(self, self.outpath() + 'output_skn.w3x')
        self.assertEqual(6, len(root.find('Includes').findall('Include')))

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output_skn.w3x'
        load(self)

        # check created objects
        self.assertTrue('testname_skl' in bpy.data.objects)
        self.assertTrue('testname_skl' in bpy.data.armatures)
        amt = bpy.data.armatures['testname_skl']
        self.assertEqual(7, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

    def test_roundtrip_no_armature(self):
        hierarchy_name = 'TestModelName'
        hierarchy = get_hierarchy(hierarchy_name)
        hierarchy.pivots = [get_roottransform(),
                            get_hierarchy_pivot(name='sword', parent=0),
                            get_hierarchy_pivot(name='soldier', parent=0),
                            get_hierarchy_pivot(name='TRUNK', parent=0)]

        meshes = [get_mesh(name='sword'),
                  get_mesh(name='soldier'),
                  get_mesh(name='TRUNK')]
        hlod = get_hlod('TestModelName', hierarchy_name)
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=1, name='containerName.sword'),
            get_hlod_sub_object(bone=2, name='containerName.soldier'),
            get_hlod_sub_object(bone=3, name='containerName.TRUNK')]
        hlod.lod_arrays[0].header.model_count = len(hlod.lod_arrays[0].sub_objects)

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output'
        create_data(self, meshes, hlod, hierarchy)

        # export
        self.filepath = self.outpath() + 'output'
        export_settings = {'mode': 'HM', 'compression': 'U', 'individual_files': False, 'create_texture_xmls': True,
                           'use_existing_skeleton': False}
        save_data(self, export_settings)

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output.w3x'
        load(self)

        # check created objects
        self.assertTrue('TestModelName' in bpy.data.objects)
        self.assertTrue('TestModelName' in bpy.data.armatures)
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
        export_settings = {'mode': 'HM', 'compression': 'U', 'individual_files': True, 'create_texture_xmls': True,
                           'use_existing_skeleton': False}
        save_data(self, export_settings)

        # remove includes
        root = find_root(self, self.outpath() + 'output_skn.w3x')
        for child in root:
            if child.tag == 'Includes':
                root.remove(child)
        write(root, self.outpath() + 'output_skn.w3x')

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
        load(self)

        # check created objects
        self.assertEqual(2, len(bpy.data.collections))

        self.assertTrue('testname_skl' in bpy.data.objects)
        self.assertTrue('testname_skl' in bpy.data.armatures)
        amt = bpy.data.armatures['testname_skl']
        self.assertEqual(7, len(amt.bones))

        self.assertFalse('sword' in bpy.data.objects)
        self.assertFalse('soldier' in bpy.data.objects)
        self.assertFalse('BOUNDINGBOX' in bpy.data.objects)

        self.assertTrue('TRUNK' in bpy.data.objects)

        # import
        self.filepath = self.outpath() + 'output_skn.sword.w3x'
        load(self)

        self.assertEqual(2, len(bpy.data.collections))

        self.assertFalse('soldier' in bpy.data.objects)
        self.assertFalse('BOUNDINGBOX' in bpy.data.objects)

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

        # import
        self.filepath = self.outpath() + 'output_skn.BOUNDINGBOX.w3x'
        load(self)

        self.assertEqual(2, len(bpy.data.collections))

        self.assertFalse('soldier' in bpy.data.objects)

        self.assertTrue('BOUNDINGBOX' in bpy.data.objects)
        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

    def test_roundtrip_hlod_only_import(self):
        hierarchy_name = 'testname_skl'
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK')]
        hlod = get_hlod(hierarchy_name, hierarchy_name)

        create_data(self, meshes, hlod, hierarchy)

        # export
        self.set_format('W3X')
        self.filepath = self.outpath() + 'output'
        export_settings = {'mode': 'HM', 'compression': 'U', 'individual_files': True, 'create_texture_xmls': True,
                           'use_existing_skeleton': False}
        save_data(self, export_settings)

        # remove includes
        root = find_root(self, self.outpath() + 'output.w3x')
        for child in root:
            if child.tag == 'Includes':
                root.remove(child)
        write(root, self.outpath() + 'output.w3x')

        # check created files
        self.assertTrue(os.path.exists(self.outpath() + 'output.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output.sword.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output.soldier.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'output.TRUNK.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'testname_skl.w3x'))
        self.assertTrue(os.path.exists(self.outpath() + 'texture.xml'))

        # reset scene
        bpy.ops.wm.read_homefile(app_template='')

        # import
        self.filepath = self.outpath() + 'output.w3x'
        load(self)

        # check created objects
        self.assertEqual(2, len(bpy.data.collections))

        self.assertTrue('testname_skl' in bpy.data.objects)
        self.assertTrue('testname_skl' in bpy.data.armatures)
        amt = bpy.data.armatures['testname_skl']
        self.assertEqual(7, len(amt.bones))

        self.assertTrue('sword' in bpy.data.objects)
        self.assertTrue('soldier' in bpy.data.objects)
        self.assertTrue('TRUNK' in bpy.data.objects)

    def test_roundtrip_mesh_is_camera_oriented(self):
        mesh_struct = get_mesh('camera_oriented')
        mesh_struct.header.attrs |= GEOMETRY_TYPE_CAMERA_ORIENTED

        create_mesh(self, mesh_struct, bpy.context.scene.collection)

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output'
        export_settings = {'mode': 'HM', 'compression': 'U', 'individual_files': True, 'create_texture_xmls': True,
                           'use_existing_skeleton': False}
        save_data(self, export_settings)

    def test_roundtrip_mesh_is_camera_aligned(self):
        mesh_struct = get_mesh('camera_aligned')
        mesh_struct.header.attrs |= GEOMETRY_TYPE_CAMERA_ALIGNED

        create_mesh(self, mesh_struct, bpy.context.scene.collection)

        self.set_format('W3X')
        self.filepath = self.outpath() + 'output'
        export_settings = {'mode': 'HM', 'compression': 'U', 'individual_files': True, 'create_texture_xmls': True,
                           'use_existing_skeleton': False}
        save_data(self, export_settings)
