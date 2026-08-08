# <pep8 compliant>
"""Find and import existing W3D animations that match a skeleton."""

import os

import bpy
from bpy.props import CollectionProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from .. import cache, utils


class FoundAnimationItem(PropertyGroup):
    key: StringProperty(name='Asset Key')
    filename: StringProperty(name='Filename')


class BFME_OT_search_animations(Operator):
    bl_idname = 'bfme.search_animations'
    bl_label = 'Search Animations'
    bl_description = 'Search the asset paths and .big archives for animations of this skeleton'

    def execute(self, context):
        scene = context.scene
        target = scene.existing_anim_target

        if target is None:
            self.report({'ERROR'}, 'Please select an armature first.')
            return {'CANCELLED'}

        skeleton_name = target.name.strip().split('.')[0]
        scene.found_animations.clear()

        search_paths = list(utils.search_paths(scene))
        if bpy.data.filepath:
            search_paths.append(os.path.dirname(bpy.data.filepath))

        utils.refresh_big_lists(scene)
        index = cache.asset_index(utils.selected_big_paths(scene), search_paths, {'.w3d'})

        needle = skeleton_name.encode('utf-8')
        name_filter = scene.existing_anim_filter.strip().lower()

        found = 0
        for key, reference in sorted(index.items()):
            filename = cache.asset_name(reference)
            lowered = filename.lower()
            if not lowered.endswith('.w3d'):
                continue
            if name_filter and name_filter not in lowered:
                continue

            # the candidate's bytes are streamed straight out of its archive, so
            # searching them costs no extraction and nothing lands on disk
            if not cache.asset_contains(reference, needle):
                continue

            item = scene.found_animations.add()
            item.filename = filename
            item.key = key
            found += 1

        if found:
            self.report({'INFO'}, f'Found {found} compatible animations.')
        else:
            self.report({'WARNING'}, f"No animations found for '{skeleton_name}'.")
        return {'FINISHED'}


class BFME_OT_import_animation(Operator):
    bl_idname = 'bfme.import_animation'
    bl_label = 'Import Animation'
    bl_description = 'Import this W3D animation and assign it to the selected skeleton'

    key: StringProperty()

    def execute(self, context):
        # the animation and the skeleton it names get written out at this point,
        # rather than the whole archive
        filepath = cache.stage_for_import(cache.cached_asset_index(), self.key)
        if filepath is None:
            self.report({'ERROR'}, f"Could not read '{self.key}'. Search again.")
            return {'CANCELLED'}

        target = context.scene.existing_anim_target

        # the W3D animation importer keyframes the target skeleton directly rather than
        # building a standalone action, so if it already has one, keyframe_insert() adds
        # to it instead of starting fresh, silently mixing the old and new animation's
        # keyframes on the same fcurves. Detach it before importing so a clean action is
        # created; only actually removed once the import has succeeded, so a failed
        # import leaves the previous animation intact
        previous_actions = self._detach_actions(target)

        actions_before = {action.name for action in bpy.data.actions}
        objects_before = {obj.name for obj in bpy.data.objects}

        try:
            result = utils.import_w3d(filepath)
        except RuntimeError as error:
            self._restore_actions(target, previous_actions)
            self.report({'ERROR'}, f'Import failed: {error}')
            return {'CANCELLED'}

        if 'FINISHED' not in result:
            self._restore_actions(target, previous_actions)
            self.report({'ERROR'}, f'Import failed for {os.path.basename(filepath)}')
            return {'CANCELLED'}

        for action in previous_actions.values():
            if action.users == 0:
                bpy.data.actions.remove(action)

        action = self._imported_action(actions_before, objects_before)
        message = f'Imported {os.path.basename(filepath)}'

        if action is not None and target is not None and target.type == 'ARMATURE':
            if not target.animation_data:
                target.animation_data_create()
            target.animation_data.action = action
            message += f" and assigned action '{action.name}' to '{target.name}'"
        else:
            message += ' (no new action found to assign)'

        self.report({'INFO'}, message)
        return {'FINISHED'}

    @staticmethod
    def _detach_actions(target):
        """Clear the target's existing actions and return them, keyed by where they came from."""
        previous = {}
        if target is None:
            return previous

        if target.animation_data and target.animation_data.action:
            previous['object'] = target.animation_data.action
            target.animation_data.action = None

        # bone visibility channels live on the armature data-block's own animation,
        # separate from the object-level pose animation above
        if target.type == 'ARMATURE' and target.data.animation_data and target.data.animation_data.action:
            previous['data'] = target.data.animation_data.action
            target.data.animation_data.action = None

        return previous

    @staticmethod
    def _restore_actions(target, previous_actions):
        if target is None:
            return
        if 'object' in previous_actions:
            if not target.animation_data:
                target.animation_data_create()
            target.animation_data.action = previous_actions['object']
        if 'data' in previous_actions:
            if not target.data.animation_data:
                target.data.animation_data_create()
            target.data.animation_data.action = previous_actions['data']

    @staticmethod
    def _imported_action(actions_before, objects_before):
        for action in bpy.data.actions:
            if action.name not in actions_before:
                return action

        for obj in bpy.data.objects:
            if obj.name in objects_before or obj.type != 'ARMATURE':
                continue
            if obj.animation_data and obj.animation_data.action:
                return obj.animation_data.action
        return None


class EXISTING_ANIMATIONS_PT_panel(Panel):
    bl_label = 'Existing Animations'
    bl_idname = 'EXISTING_ANIMATIONS_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'W3D Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, 'existing_anim_target')
        layout.prop(scene, 'existing_anim_filter')
        layout.row().operator('bfme.search_animations', icon='VIEWZOOM')

        if not len(scene.found_animations):
            return

        box = layout.box()
        box.label(text=f'Found {len(scene.found_animations)} files:')
        for item in scene.found_animations:
            row = box.row(align=True)
            row.label(text=item.filename)
            row.operator('bfme.import_animation', text='Import', icon='IMPORT').key = item.key


def update_anim_target(self, _context):
    target = self.existing_anim_target
    if target is None:
        return

    name = target.name.strip().split('.')[0]
    self.existing_anim_filter = (name[:-4] if name.upper().endswith('_SKL') else name) + '_'


CLASSES = (
    FoundAnimationItem,
    BFME_OT_search_animations,
    BFME_OT_import_animation,
    EXISTING_ANIMATIONS_PT_panel)

SCENE_PROPERTIES = ('existing_anim_target', 'found_animations', 'existing_anim_filter')


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    scene = bpy.types.Scene
    scene.existing_anim_target = PointerProperty(
        type=bpy.types.Object,
        name='Skeleton',
        description='The armature to find animations for',
        poll=lambda self, obj: obj.type == 'ARMATURE',
        update=update_anim_target)
    scene.found_animations = CollectionProperty(type=FoundAnimationItem)
    scene.existing_anim_filter = StringProperty(
        name='Filter Name', description='Only show files containing this string', default='')


def unregister():
    for name in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
