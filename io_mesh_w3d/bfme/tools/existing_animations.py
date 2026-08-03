# <pep8 compliant>
"""Find and import existing W3D animations that match a skeleton."""

import os

import bpy
from bpy.props import CollectionProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from .. import cache, utils

SCAN_CHUNK_SIZE = 256 * 1024


def file_contains(filepath, needle, chunk_size=SCAN_CHUNK_SIZE):
    """Whether the file contains the byte string, without reading it all at once.

    A .w3d can be tens of megabytes and a search sweeps thousands of them, so the
    file is streamed and only the tail of the previous chunk is kept around so a
    match spanning a chunk boundary is still found.
    """
    overlap = len(needle) - 1
    if overlap < 0:
        return True

    try:
        with open(filepath, 'rb') as file:
            tail = b''
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    return False

                buffer = tail + chunk
                if needle in buffer:
                    return True

                # carry over the tail of the whole buffer, not just of this chunk,
                # so nothing is dropped when a chunk is shorter than the needle
                tail = buffer[-overlap:] if overlap else b''
    except OSError:
        return False


class FoundAnimationItem(PropertyGroup):
    filepath: StringProperty(name='Filepath')
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

        directories = set(utils.search_paths(scene))
        if bpy.data.filepath:
            directories.add(os.path.dirname(bpy.data.filepath))

        utils.refresh_big_lists(scene)
        big_paths = utils.selected_big_paths(scene)
        if big_paths:
            if cache.extract_bigs(big_paths, {'.w3d'}) and os.path.isdir(cache.BIG_CACHE_DIR):
                directories.add(cache.BIG_CACHE_DIR)

        needle = skeleton_name.encode('utf-8')
        name_filter = scene.existing_anim_filter.strip().lower()

        found = 0
        for directory in directories:
            if not os.path.isdir(directory):
                continue
            for root, _, files in os.walk(directory):
                for filename in files:
                    lowered = filename.lower()
                    if not lowered.endswith('.w3d'):
                        continue
                    if name_filter and name_filter not in lowered:
                        continue

                    filepath = os.path.join(root, filename)
                    if not file_contains(filepath, needle):
                        continue

                    item = scene.found_animations.add()
                    item.filename = filename
                    item.filepath = filepath
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

    filepath: StringProperty()

    def execute(self, context):
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({'ERROR'}, 'File not found.')
            return {'CANCELLED'}

        target = context.scene.existing_anim_target
        actions_before = {action.name for action in bpy.data.actions}
        objects_before = {obj.name for obj in bpy.data.objects}

        try:
            result = utils.import_w3d(self.filepath)
        except RuntimeError as error:
            self.report({'ERROR'}, f'Import failed: {error}')
            return {'CANCELLED'}

        if 'FINISHED' not in result:
            self.report({'ERROR'}, f'Import failed for {os.path.basename(self.filepath)}')
            return {'CANCELLED'}

        action = self._imported_action(actions_before, objects_before)
        message = f'Imported {os.path.basename(self.filepath)}'

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
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_parent_id = 'SCENE_PT_bfme'

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
            row.operator('bfme.import_animation', text='Import', icon='IMPORT').filepath = item.filepath


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
