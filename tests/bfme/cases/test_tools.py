# <pep8 compliant>
# Tests for the BfMe tool helpers that do not need a modal operator to run.

import os
import shutil
import tempfile

import bpy
import numpy as np
from mathutils import Vector

from io_mesh_w3d.bfme import utils
from io_mesh_w3d.bfme.tools import existing_animations, export_settings, model_browser, w3d_tools
from io_mesh_w3d.common.utils.helpers import iter_action_fcurves
from tests.utils import TestCase


class TestExistingAnimationsActionHandling(TestCase):
    """The W3D animation importer keyframes the target skeleton directly rather than
    building a standalone action, so re-importing onto a rig that already has one used
    to mix the new keyframes into the old action instead of replacing it. These test
    the detach/restore helpers that keep the two separate.
    """

    def create_rig_with_action(self):
        armature_data = bpy.data.armatures.new('rig')
        rig = bpy.data.objects.new('rig', armature_data)
        bpy.context.scene.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig

        bpy.ops.object.mode_set(mode='EDIT')
        bone = armature_data.edit_bones.new('bone1')
        bone.head = (0, 0, 0)
        bone.tail = (0, 1, 0)
        bpy.ops.object.mode_set(mode='OBJECT')

        pose_bone = rig.pose.bones['bone1']
        pose_bone.location = (1, 0, 0)
        pose_bone.keyframe_insert(data_path='location', frame=0)
        return rig

    def test_detach_actions_clears_the_object_level_action(self):
        rig = self.create_rig_with_action()
        original = rig.animation_data.action

        previous = existing_animations.BFME_OT_import_animation._detach_actions(rig)

        self.assertIsNone(rig.animation_data.action)
        self.assertEqual(original, previous['object'])

    def test_detach_actions_clears_the_data_level_action(self):
        rig = self.create_rig_with_action()
        rig.data.animation_data_create()
        rig.data.animation_data.action = bpy.data.actions.new('bone_visibility')

        previous = existing_animations.BFME_OT_import_animation._detach_actions(rig)

        self.assertIsNone(rig.data.animation_data.action)
        self.assertEqual('bone_visibility', previous['data'].name)

    def test_detach_actions_of_a_rig_without_animation(self):
        armature_data = bpy.data.armatures.new('rig')
        rig = bpy.data.objects.new('rig', armature_data)
        bpy.context.scene.collection.objects.link(rig)

        self.assertEqual({}, existing_animations.BFME_OT_import_animation._detach_actions(rig))

    def test_detach_actions_of_none(self):
        self.assertEqual({}, existing_animations.BFME_OT_import_animation._detach_actions(None))

    def test_restore_actions_reattaches_the_previous_action(self):
        rig = self.create_rig_with_action()
        original = rig.animation_data.action
        previous = existing_animations.BFME_OT_import_animation._detach_actions(rig)

        existing_animations.BFME_OT_import_animation._restore_actions(rig, previous)

        self.assertEqual(original, rig.animation_data.action)

    def test_detaching_before_reimport_keeps_the_previous_keyframes_intact(self):
        """Reproduces the reported bug: without detaching first, importing a second
        animation onto the same rig overwrites the first animation's keyframes because
        keyframe_insert() adds to whatever action is already assigned.
        """
        rig = self.create_rig_with_action()
        original_action = rig.animation_data.action
        pose_bone = rig.pose.bones['bone1']

        existing_animations.BFME_OT_import_animation._detach_actions(rig)

        # simulate what the W3D animation importer does for a second animation file
        pose_bone.location = (5, 5, 5)
        pose_bone.keyframe_insert(data_path='location', frame=0)
        new_action = rig.animation_data.action

        self.assertNotEqual(original_action, new_action)

        # read the detached action back through a throwaway carrier, since reading its
        # fcurves requires an animation_data with both the action and its slot bound,
        # and assigning .action alone doesn't rebind .action_slot
        carrier = bpy.data.objects.new('carrier', bpy.data.meshes.new('carrier'))
        carrier.animation_data_create()
        carrier.animation_data.action = original_action
        carrier.animation_data.action_slot = original_action.slots[0]
        original_fcurve = next(
            fc for fc in iter_action_fcurves(carrier.animation_data)
            if fc.data_path == 'pose.bones["bone1"].location' and fc.array_index == 0)
        self.assertEqual(1.0, original_fcurve.keyframe_points[0].co.y)


class TestPreviewIndex(TestCase):
    def setUp(self):
        super().setUp()
        self.directory = tempfile.mkdtemp(prefix='bfme-preview-')
        self._original = model_browser.PREVIEW_INDEX_FILE
        model_browser.PREVIEW_INDEX_FILE = os.path.join(self.directory, 'index.json')
        model_browser.invalidate_preview_index()

    def tearDown(self):
        model_browser.PREVIEW_INDEX_FILE = self._original
        model_browser.invalidate_preview_index()
        shutil.rmtree(self.directory, ignore_errors=True)
        super().tearDown()

    def write(self, name, content=b'data'):
        path = os.path.join(self.directory, name)
        with open(path, 'wb') as file:
            file.write(content)
        return path

    def test_file_signature(self):
        path = self.write('model.w3d')

        signature = model_browser.file_signature(path)

        self.assertEqual(2, len(signature))
        self.assertEqual(os.path.getsize(path), signature[1])

    def test_file_signature_of_missing_file(self):
        self.assertIsNone(model_browser.file_signature(os.path.join(self.directory, 'gone.w3d')))

    def test_preview_is_invalid_without_a_preview_file(self):
        model = self.write('model.w3d')

        self.assertFalse(model_browser.is_preview_valid(model, os.path.join(self.directory, 'gone.png')))

    def test_preview_is_invalid_without_an_index_entry(self):
        model = self.write('model.w3d')
        preview = self.write('model.png')

        self.assertFalse(model_browser.is_preview_valid(model, preview))

    def test_preview_is_valid_after_being_indexed(self):
        model = self.write('model.w3d')
        preview = self.write('model.png')

        model_browser.update_preview_index(model, preview)

        self.assertTrue(model_browser.is_preview_valid(model, preview))

    def test_preview_becomes_invalid_when_the_model_changes(self):
        model = self.write('model.w3d')
        preview = self.write('model.png')
        model_browser.update_preview_index(model, preview)

        self.write('model.w3d', b'changed content, different size')

        self.assertFalse(model_browser.is_preview_valid(model, preview))

    def test_preview_index_roundtrip(self):
        model = self.write('model.w3d')
        preview = self.write('model.png')
        model_browser.update_preview_index(model, preview)

        model_browser.invalidate_preview_index()

        self.assertIn(model, model_browser.load_preview_index())


class TestChunkedFileSearch(TestCase):
    def setUp(self):
        super().setUp()
        self.directory = tempfile.mkdtemp(prefix='bfme-search-')

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)
        super().tearDown()

    def write(self, content):
        path = os.path.join(self.directory, 'model.w3d')
        with open(path, 'wb') as file:
            file.write(content)
        return path

    def test_finds_a_match(self):
        path = self.write(b'header' + b'SKELETON_NAME' + b'trailer')

        self.assertTrue(existing_animations.file_contains(path, b'SKELETON_NAME'))

    def test_reports_a_miss(self):
        path = self.write(b'nothing to see here')

        self.assertFalse(existing_animations.file_contains(path, b'SKELETON_NAME'))

    def test_finds_a_match_across_a_chunk_boundary(self):
        needle = b'SKELETON_NAME'
        # the needle straddles the boundary, which a naive chunked scan would miss
        path = self.write(b'a' * 9 + needle + b'b' * 10)

        self.assertTrue(existing_animations.file_contains(path, needle, chunk_size=10))

    def test_missing_file_is_not_a_match(self):
        self.assertFalse(existing_animations.file_contains(
            os.path.join(self.directory, 'gone.w3d'), b'x'))


class TestTextureExtensionReplacement(TestCase):
    def setUp(self):
        super().setUp()
        self.directory = tempfile.mkdtemp(prefix='bfme-export-')

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)
        super().tearDown()

    def replace(self, content):
        path = os.path.join(self.directory, 'model.w3d')
        with open(path, 'wb') as file:
            file.write(content)
        export_settings.BFME_OT_export_model.replace_texture_extensions(path)
        with open(path, 'rb') as file:
            return file.read()

    def test_replaces_every_occurrence(self):
        self.assertEqual(b'a.tga|b.tga|c.tga', self.replace(b'a.dds|b.dds|c.dds'))

    def test_replaces_upper_and_mixed_case(self):
        self.assertEqual(b'a.TGA b.Tga', self.replace(b'a.DDS b.Dds'))

    def test_leaves_unrelated_content_alone(self):
        self.assertEqual(b'a.tga b.png', self.replace(b'a.tga b.png'))


class TestGeometryAnalysis(TestCase):
    def create_mesh(self, name, location, size=1.0):
        mesh = bpy.data.meshes.new(name)
        offsets = [(-size, -size, -size), (size, -size, -size), (size, size, -size), (-size, size, -size),
                   (-size, -size, size), (size, -size, size), (size, size, size), (-size, size, size)]
        vertices = [(location[0] + x, location[1] + y, location[2] + z) for x, y, z in offsets]
        mesh.from_pydata(vertices, [], [(0, 1, 2, 3), (4, 5, 6, 7)])
        mesh.update()

        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj

    def test_world_bounds(self):
        obj = self.create_mesh('cube', (0, 0, 0), size=2.0)

        minimum, maximum = utils.world_bounds([obj])

        self.assertEqual(Vector((-2, -2, -2)), minimum)
        self.assertEqual(Vector((2, 2, 2)), maximum)

    def test_world_bounds_respects_the_object_transform(self):
        obj = self.create_mesh('cube', (0, 0, 0), size=1.0)
        obj.location = (10, 0, 0)
        bpy.context.view_layer.update()

        minimum, maximum = utils.world_bounds([obj])

        self.assertEqual(9, minimum.x)
        self.assertEqual(11, maximum.x)

    def test_world_bounds_of_nothing(self):
        self.assertEqual((None, None), utils.world_bounds([]))

    def test_max_world_vertex_z(self):
        first = self.create_mesh('low', (0, 0, 0), size=1.0)
        second = self.create_mesh('high', (0, 0, 10), size=1.0)

        self.assertEqual(11, utils.max_world_vertex_z([first, second]))

    def test_max_world_vertex_z_of_nothing(self):
        self.assertIsNone(utils.max_world_vertex_z([]))

    def test_analyze_meshes_reports_bounds(self):
        obj = self.create_mesh('cube', (0, 0, 0), size=2.0)

        analysis = w3d_tools.analyze_meshes([obj])

        self.assertEqual(Vector((4, 4, 4)), analysis['size'])
        self.assertEqual(Vector((0, 0, 0)), analysis['center'])
        self.assertTrue(analysis['is_round_base'])

    def test_analyze_meshes_without_vertices(self):
        mesh = bpy.data.meshes.new('empty')
        obj = bpy.data.objects.new('empty', mesh)
        bpy.context.scene.collection.objects.link(obj)

        self.assertIsNone(w3d_tools.analyze_meshes([obj]))

    def test_detect_z_regions_of_a_solid_column(self):
        coords = np.column_stack([
            np.zeros(100), np.zeros(100), np.linspace(0.0, 10.0, 100)])

        regions = w3d_tools.detect_z_regions(coords, 0.0, 10.0)

        self.assertEqual(1, len(regions))
        self.assertAlmostEqual(0.0, regions[0]['z_min'])
        self.assertAlmostEqual(10.0, regions[0]['z_max'])

    def test_detect_z_regions_of_a_flat_model(self):
        coords = np.zeros((10, 3))

        self.assertEqual([], w3d_tools.detect_z_regions(coords, 0.0, 0.0))

    def test_detect_cylindrical_features_of_a_ring(self):
        angles = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        coords = np.column_stack([np.cos(angles) * 3.0, np.sin(angles) * 3.0, np.zeros(64)])
        regions = [{'z_min': -1.0, 'z_max': 1.0, 'z_center': 0.0, 'height': 2.0}]

        features = w3d_tools.detect_cylindrical_features(coords, regions)

        self.assertEqual(1, len(features))
        self.assertAlmostEqual(3.0, features[0]['radius'], places=5)

    def test_detect_cylindrical_features_ignores_elongated_shapes(self):
        # a long thin bar has a wildly varying radius, unlike a tower
        rng = np.random.default_rng(0)
        coords = np.column_stack([
            rng.uniform(-10.0, 10.0, 200), rng.uniform(-0.5, 0.5, 200), np.zeros(200)])
        regions = [{'z_min': -1.0, 'z_max': 1.0, 'z_center': 0.0, 'height': 2.0}]

        self.assertEqual([], w3d_tools.detect_cylindrical_features(coords, regions))

    def test_detect_corner_features(self):
        rng = np.random.default_rng(1)
        coords = rng.uniform(-10.0, 10.0, size=(500, 3))

        corners = w3d_tools.detect_corner_features(coords, Vector((0, 0, 0)), Vector((20, 20, 20)))

        self.assertEqual(8, len(corners))

    def test_distributed_surface_positions_count(self):
        obj = self.create_mesh('cube', (0, 0, 0), size=5.0)

        positions = w3d_tools.distributed_surface_positions([obj], 4)

        self.assertEqual(4, len(positions))
        for position in positions:
            self.assertIsInstance(position, Vector)

    def test_distributed_surface_positions_of_nothing(self):
        self.assertEqual([], w3d_tools.distributed_surface_positions([], 4))

    def test_generate_ini_text(self):
        obj = self.create_mesh('GEOMETRY_MainBody', (0, 0, 0))
        obj.data.object_type = 'GEOMETRY'
        obj.data.geometry_type = 'BOX'
        obj.scale = (2.0, 3.0, 4.0)

        text = w3d_tools.generate_ini_text([obj])

        self.assertIn('Geometry\t\t\t\t= BOX', text)
        self.assertIn('GeometryName\t\t\t= GEOMETRY_MainBody', text)
        self.assertIn('GeometryMajorRadius\t\t= 2.000', text)
        self.assertIn('GeometryMinorRadius\t\t= 3.000', text)
        self.assertIn('GeometryHeight\t\t\t= 4.000', text)

    def test_generate_ini_text_for_a_cylinder(self):
        obj = self.create_mesh('GEOMETRY_Tower_01', (0, 0, 0))
        obj.data.object_type = 'GEOMETRY'
        obj.data.geometry_type = 'CYLINDER'
        obj.scale = (2.0, 2.0, 5.0)

        text = w3d_tools.generate_ini_text([obj])

        self.assertIn('GeometryMajorRadius\t\t= 2.000', text)
        self.assertIn('GeometryHeight\t\t\t= 10.000', text)
        self.assertNotIn('GeometryMinorRadius', text)

    def test_generate_ini_text_keeps_the_z_offset_at_zero(self):
        obj = self.create_mesh('GEOMETRY_Corner_01', (0, 0, 0))
        obj.data.object_type = 'GEOMETRY'
        obj.data.geometry_type = 'BOX'
        obj.location = (5.0, 7.0, 9.0)

        text = w3d_tools.generate_ini_text([obj])

        self.assertIn('GeometryOffset\t\t\t= X:5.000 Y:7.000 Z:0.000', text)
