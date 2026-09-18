# <pep8 compliant>
# Tests for the BfMe tool helpers that do not need a modal operator to run.

import os
import shutil
import tempfile
from unittest.mock import patch

import bpy
import numpy as np
from bpy.props import CollectionProperty
from mathutils import Vector

from io_mesh_w3d.bfme import cache, utils
from io_mesh_w3d.bfme.tools import destroy_animation, existing_animations, export_settings, model_browser, w3d_tools
from io_mesh_w3d.common.utils.helpers import iter_action_fcurves
from tests.bfme.cases.test_cache import w3d_model, write_big_archive
from tests.utils import TestCase


class TestReplaceAction(TestCase):
    def test_creates_a_fresh_action_when_none_exists(self):
        action = utils.replace_action('build_up')

        self.assertEqual('build_up', action.name)

    def test_reusing_a_name_does_not_suffix_it(self):
        first = utils.replace_action('build_up')

        second = utils.replace_action('build_up')

        self.assertEqual('build_up', second.name)
        self.assertNotEqual(first, second)

    def test_the_old_action_of_that_name_is_removed(self):
        first = utils.replace_action('build_up')
        first_name = first.name

        utils.replace_action('build_up')

        self.assertNotIn(first_name, [a.name for a in bpy.data.actions if a == first])
        self.assertEqual(1, len([a for a in bpy.data.actions if a.name == 'build_up']))

    def test_does_not_touch_an_action_of_a_different_name(self):
        other = bpy.data.actions.new('destroy')

        utils.replace_action('build_up')

        self.assertIn(other, list(bpy.data.actions))


class TestDestroySplitCountEstimate(TestCase):
    """The automatic piece count used to leave real assets fractured into far more
    sub-objects than a destruction animation needs; each size bucket now computes
    about half of what it used to.
    """

    def child_of_size(self, armature, size):
        mesh = bpy.data.meshes.new('piece')
        mesh.from_pydata([(0, 0, 0), (size, 0, 0), (0, size, 0), (0, 0, size)], [], [(0, 1, 2), (0, 1, 3)])
        mesh.update()
        obj = bpy.data.objects.new('piece', mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = armature
        return obj

    def test_split_counts_by_size_bucket(self):
        armature_data = bpy.data.armatures.new('rig')
        armature = bpy.data.objects.new('rig', armature_data)
        bpy.context.scene.collection.objects.link(armature)

        for size, expected in ((10, 2), (40, 2), (80, 4), (150, 8), (500, 16)):
            for obj in list(armature.children):
                bpy.data.objects.remove(obj, do_unlink=True)
            self.child_of_size(armature, size)

            bpy.context.scene.destroy_target = armature
            destroy_animation.update_destroy_settings(None, bpy.context)

            item = bpy.context.scene.splitting_object_settings[0]
            self.assertEqual(expected, item.split_count, f'size {size}')


class TestRepeatedAnimationGeneration(TestCase):
    """Create Build-up/Destroy Animation used to drift to 'name.001', 'name.002', ...
    on every repeated click instead of keeping the exact configured name, since
    bpy.data.actions.new() suffixes rather than replacing a name already taken.
    """

    def create_rig(self, name='rig'):
        armature_data = bpy.data.armatures.new(name)
        rig = bpy.data.objects.new(name, armature_data)
        bpy.context.scene.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig

        bpy.ops.object.mode_set(mode='EDIT')
        bone = armature_data.edit_bones.new('bone1')
        bone.head = (0, 0, 0)
        bone.tail = (0, 1, 0)
        bpy.ops.object.mode_set(mode='OBJECT')
        return rig

    def test_build_up_animation_keeps_the_exact_name_when_run_twice(self):
        scene = bpy.context.scene
        scene.build_up_target = self.create_rig()
        scene.build_up_name = 'hb_w_walls_a'

        bpy.ops.bfme.build_up_animation()
        bpy.ops.bfme.build_up_animation()

        self.assertEqual(['hb_w_walls_a'], sorted(a.name for a in bpy.data.actions))

    def test_destroy_animation_keeps_the_exact_name_when_run_twice(self):
        scene = bpy.context.scene
        scene.destroy_target = self.create_rig()
        scene.destroy_name = 'hb_w_walls_d'

        bpy.ops.bfme.destroy_animation()
        bpy.ops.bfme.destroy_animation()

        self.assertEqual(['hb_w_walls_d'], sorted(a.name for a in bpy.data.actions))


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
        # and assigning .action alone doesn't rebind .action_slot. 'Action.slots' only
        # exists from Blender 4.4's slotted actions onward; older versions have no
        # such concept and read fcurves straight off the action once it is assigned
        carrier = bpy.data.objects.new('carrier', bpy.data.meshes.new('carrier'))
        carrier.animation_data_create()
        carrier.animation_data.action = original_action
        if hasattr(original_action, 'slots'):
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

    def loose_reference(self, name='model.w3d'):
        return [cache.REF_FILE, self.write(name)]

    def test_reference_signature_of_a_loose_file(self):
        reference = self.loose_reference()

        signature = model_browser.reference_signature(reference)

        self.assertEqual(2, len(signature))
        self.assertEqual(os.path.getsize(reference[1]), signature[1])

    def test_reference_signature_of_an_archive_entry(self):
        archive = self.write('assets.big', b'x' * 64)

        signature = model_browser.reference_signature([cache.REF_BIG, archive, 'model.w3d', 20, 9])

        # the archive's own stamp plus the entry's byte range, so the signature can
        # be taken without extracting the entry
        self.assertEqual(4, len(signature))
        self.assertEqual([20, 9], signature[2:])

    def test_reference_signature_of_a_missing_file(self):
        self.assertIsNone(model_browser.reference_signature(
            [cache.REF_FILE, os.path.join(self.directory, 'gone.w3d')]))

    def test_reference_signature_of_nothing(self):
        self.assertIsNone(model_browser.reference_signature(None))

    def test_preview_is_invalid_without_a_preview_file(self):
        reference = self.loose_reference()

        self.assertFalse(model_browser.is_preview_valid(
            'model', reference, os.path.join(self.directory, 'gone.png')))

    def test_preview_is_invalid_without_an_index_entry(self):
        reference = self.loose_reference()
        preview = self.write('model.png')

        self.assertFalse(model_browser.is_preview_valid('model', reference, preview))

    def test_preview_is_valid_after_being_indexed(self):
        reference = self.loose_reference()
        preview = self.write('model.png')

        model_browser.update_preview_index('model', reference, preview)

        self.assertTrue(model_browser.is_preview_valid('model', reference, preview))

    def test_preview_becomes_invalid_when_the_model_changes(self):
        reference = self.loose_reference()
        preview = self.write('model.png')
        model_browser.update_preview_index('model', reference, preview)

        self.write('model.w3d', b'changed content, different size')

        self.assertFalse(model_browser.is_preview_valid('model', reference, preview))

    def test_preview_becomes_invalid_when_the_entry_moves_inside_the_archive(self):
        archive = self.write('assets.big', b'x' * 64)
        preview = self.write('model.png')
        model_browser.update_preview_index('model', [cache.REF_BIG, archive, 'model.w3d', 20, 9], preview)

        moved = [cache.REF_BIG, archive, 'model.w3d', 40, 9]

        self.assertFalse(model_browser.is_preview_valid('model', moved, preview))

    def test_preview_index_roundtrip(self):
        reference = self.loose_reference()
        preview = self.write('model.png')
        model_browser.update_preview_index('model', reference, preview)

        model_browser.invalidate_preview_index()

        self.assertIn('model', model_browser.load_preview_index())

    def test_preview_rendered_by_an_older_version_is_invalid(self):
        reference = self.loose_reference()
        preview = self.write('model.png')
        model_browser.update_preview_index('model', reference, preview)

        # what an entry written before previews carried a version looks like
        model_browser.load_preview_index()['model'].pop('version', None)

        self.assertFalse(model_browser.is_preview_valid('model', reference, preview))


class TestModelList(TestCase):
    def setUp(self):
        super().setUp()
        self.directory = tempfile.mkdtemp(prefix='bfme-models-')
        cache.invalidate_asset_index()

    def tearDown(self):
        cache.invalidate_asset_index()
        shutil.rmtree(self.directory, ignore_errors=True)
        super().tearDown()

    def write(self, subdirectory, name):
        path = os.path.join(self.directory, subdirectory, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as file:
            file.write(b'data')
        return os.path.dirname(path)

    def test_a_model_is_listed_when_a_texture_shares_its_name(self):
        models = self.write('w3d', 'hu_r_treb.w3d')
        # the later search path, so the texture is what the flat index keeps
        textures = self.write('compiledtextures', 'hu_r_treb.dds')
        sources = [(models, 'Mod', [models]), (textures, 'Textures', [textures])]

        rows = model_browser._collect_w3d_models([], [models, textures], sources, force_refresh=True)

        # a source without any models gets no header either
        self.assertEqual([('Mod', '', models, True), ('hu_r_treb.w3d', 'hu_r_treb', models, False)], rows)

    def test_a_model_shipped_by_two_sources_is_listed_under_each(self):
        edain = self.write('Edain-Mod', 'hu_r_treb.w3d')
        self.write('Edain-Mod', 'edain_only.w3d')
        aotr = self.write('aotr', 'hu_r_treb.w3d')
        sources = [(edain, 'Edain-Mod', [edain]), (aotr, 'aotr', [aotr])]

        rows = model_browser._collect_w3d_models([], [edain, aotr], sources, force_refresh=True)

        self.assertEqual([
            ('Edain-Mod', '', edain, True),
            ('edain_only.w3d', 'edain_only', edain, False),
            ('hu_r_treb.w3d', 'hu_r_treb', edain, False),
            ('aotr', '', aotr, True),
            ('hu_r_treb.w3d', 'hu_r_treb', aotr, False)], rows)

    def test_a_game_source_lists_the_copy_of_its_highest_priority_archive_once(self):
        patch = write_big_archive(os.path.join(self.directory, 'patch.big'), {'Model.w3d': b'PATCH'})
        base = write_big_archive(os.path.join(self.directory, 'base.big'), {'model.w3d': b'BASE'})
        sources = [('bfme2', 'BfMe 2', [patch, base])]

        rows = model_browser._collect_w3d_models([patch, base], [], sources, force_refresh=True)

        self.assertEqual([('BfMe 2', '', 'bfme2', True), ('Model.w3d', 'model', 'bfme2', False)], rows)

    def test_importing_a_model_tags_the_objects_it_created_with_where_it_came_from(self):
        """Export Settings' Auto-Detect falls back to this path when the scene has
        never been saved, but nothing ever wrote it until now.
        """
        directory = self.write('w3d', 'model.w3d')
        sources = [(directory, 'Mod', [directory])]
        model_browser._collect_w3d_models([], [directory], sources, force_refresh=True)

        def fake_import(_filepath):
            new_object = bpy.data.objects.new('imported_piece', bpy.data.meshes.new('imported_piece'))
            bpy.context.scene.collection.objects.link(new_object)
            return {'FINISHED'}

        with patch.object(model_browser.utils, 'import_w3d', side_effect=fake_import):
            result = bpy.ops.w3d.import_model(key='model', source=directory)

        self.assertEqual({'FINISHED'}, result)
        # re-fetched: bpy.ops calls can invalidate Python references held from before them
        created = bpy.data.objects['imported_piece']
        self.assertEqual(os.path.join(self.directory, 'w3d'), created.get('bfme_import_path'))

    def test_recorded_import_path_is_the_models_own_folder_even_when_staged(self):
        """The common real layout: a mod's models and its textures sit in separate
        folders (e.g. 'art/w3d/hb' and 'art/compiledtextures/hb'), so a model naming
        a texture from the other folder cannot be imported in place and gets staged
        into the cache directory instead - and 'bfme_import_path' used to be read
        back off *that* staged location instead of the model's real source folder.
        """
        models_dir = os.path.join(self.directory, 'w3d')
        textures_dir = os.path.join(self.directory, 'compiledtextures')
        os.makedirs(models_dir)
        os.makedirs(textures_dir)
        with open(os.path.join(models_dir, 'model.w3d'), 'wb') as file:
            file.write(w3d_model(textures=['skin.dds']))
        with open(os.path.join(textures_dir, 'skin.dds'), 'wb') as file:
            file.write(b'SKIN')

        sources = [(models_dir, 'Mod', [models_dir, textures_dir])]
        model_browser._collect_w3d_models([], [models_dir, textures_dir], sources, force_refresh=True)

        def fake_import(_filepath):
            new_object = bpy.data.objects.new('imported_piece', bpy.data.meshes.new('imported_piece'))
            bpy.context.scene.collection.objects.link(new_object)
            return {'FINISHED'}

        with patch.object(model_browser.utils, 'import_w3d', side_effect=fake_import):
            bpy.ops.w3d.import_model(key='model', source=models_dir)

        created = bpy.data.objects['imported_piece']
        self.assertEqual(models_dir, created.get('bfme_import_path'))


class TestModelListStorage(TestCase):
    def test_the_model_list_is_not_kept_on_the_scene(self):
        """Blender finds the path of a property on a scene's collection item, which the
        UI does on every edit of it, by searching the scene's custom data. With the
        model list kept on the scene that took seconds on a full install, and every
        edit in e.g. the build-up animation's per-bone timings waited for it.
        """
        for name in model_browser.LIST_PROPERTIES:
            self.assertFalse(hasattr(bpy.types.Scene, name))
            self.assertTrue(hasattr(bpy.types.WindowManager, name))

    def test_a_model_list_saved_on_the_scene_by_an_earlier_version_is_dropped(self):
        scene = bpy.context.scene
        # stored the way an earlier version did, then no longer registered on the scene
        bpy.types.Scene.w3d_models = CollectionProperty(type=model_browser.W3DModelItem)
        model_browser._add_rows(scene.w3d_models, [('model.w3d', 'model', 'source', False)])
        del bpy.types.Scene.w3d_models

        model_browser.drop_scene_model_list()

        bpy.types.Scene.w3d_models = CollectionProperty(type=model_browser.W3DModelItem)
        try:
            self.assertFalse(scene.is_property_set('w3d_models'))
        finally:
            del bpy.types.Scene.w3d_models


class TestAssetSources(TestCase):
    def test_source_label_skips_folder_names_that_say_nothing_about_the_mod(self):
        root = os.path.join('C:' + os.sep, 'Modding')

        self.assertEqual('Edain-Mod', utils.source_label(os.path.join(root, 'Edain-Mod', '_mod', 'art') + os.sep))
        self.assertEqual('aotr', utils.source_label(os.path.join(root, 'AOTR8.0', 'aotr', 'art')))


class TestAutoConfigureExport(TestCase):
    def create_armature(self, name, collection=None):
        armature_data = bpy.data.armatures.new(name)
        rig = bpy.data.objects.new(name, armature_data)
        (collection or bpy.context.scene.collection).objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        return rig

    def settings(self):
        return bpy.context.scene.bfme_export_settings

    def test_collection_matches_armature_and_no_animation_exports_as_hierarchical_model(self):
        collection = bpy.data.collections.new('HB_W_STALLS')
        bpy.context.scene.collection.children.link(collection)
        self.create_armature('HB_W_STALLS', collection)

        bpy.ops.bfme.auto_configure_export()

        settings = self.settings()
        self.assertEqual('HM', settings.mode)
        self.assertFalse(settings.use_existing_skeleton)
        self.assertEqual('HB_W_STALLS', settings.export_name)

    def test_collection_differs_from_armature_and_no_animation_uses_existing_skeleton(self):
        collection = bpy.data.collections.new('HB_W_STALLS_props')
        bpy.context.scene.collection.children.link(collection)
        self.create_armature('HB_W_STALLS', collection)

        bpy.ops.bfme.auto_configure_export()

        settings = self.settings()
        self.assertEqual('HM', settings.mode)
        self.assertTrue(settings.use_existing_skeleton)
        self.assertEqual('HB_W_STALLS_props', settings.export_name)

    def test_collection_matches_armature_and_has_animation_exports_as_ham_named_after_it(self):
        collection = bpy.data.collections.new('HB_W_STALLS')
        bpy.context.scene.collection.children.link(collection)
        rig = self.create_armature('HB_W_STALLS', collection)
        rig.animation_data_create()
        rig.animation_data.action = bpy.data.actions.new('hb_w_walls_a')

        bpy.ops.bfme.auto_configure_export()

        settings = self.settings()
        self.assertEqual('HAM', settings.mode)
        # left unchecked as specified, even though the exporter then renames the
        # embedded hierarchy to 'hb_w_walls_a' and the game no longer recognises
        # it as HB_W_STALLS's own animation - a deliberate, confirmed trade-off
        self.assertFalse(settings.use_existing_skeleton)
        self.assertEqual('hb_w_walls_a', settings.export_name)

    def test_collection_differs_from_armature_but_has_animation_falls_back_to_hierarchical_model(self):
        collection = bpy.data.collections.new('HB_W_STALLS_props')
        bpy.context.scene.collection.children.link(collection)
        rig = self.create_armature('HB_W_STALLS', collection)
        rig.animation_data_create()
        rig.animation_data.action = bpy.data.actions.new('hb_w_walls_a')

        bpy.ops.bfme.auto_configure_export()

        settings = self.settings()
        self.assertEqual('HM', settings.mode)
        self.assertFalse(settings.use_existing_skeleton)
        self.assertEqual('HB_W_STALLS_props', settings.export_name)

    def test_path_prefers_the_saved_blend_files_directory(self):
        rig = self.create_armature('HB_W_STALLS')
        # a real, existing decoy the saved location must still win over
        decoy = os.path.join(self.outpath(), 'decoy')
        os.makedirs(decoy, exist_ok=True)
        rig['bfme_import_path'] = decoy
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(self.outpath(), 'scene.blend'))

        bpy.ops.bfme.auto_configure_export()

        self.assertEqual(os.path.normpath(self.outpath()), os.path.normpath(self.settings().export_path))

    def test_path_falls_back_to_where_the_model_was_imported_from(self):
        rig = self.create_armature('HB_W_STALLS')
        rig['bfme_import_path'] = self.outpath().rstrip(os.sep)

        bpy.ops.bfme.auto_configure_export()

        self.assertEqual(self.outpath().rstrip(os.sep), self.settings().export_path)

    def test_path_is_empty_without_a_saved_file_or_a_known_import_path(self):
        self.create_armature('HB_W_STALLS')

        bpy.ops.bfme.auto_configure_export()

        self.assertEqual('', self.settings().export_path)


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
