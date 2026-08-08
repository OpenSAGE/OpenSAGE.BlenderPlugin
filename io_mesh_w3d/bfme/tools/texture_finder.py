# <pep8 compliant>
"""Asset search paths and the texture finder.

Reconnects images whose files went missing by looking them up in the asset cache,
which is filled from the configured search paths and the selected .big archives.
"""

import os
import threading

import bpy
from bpy.types import Operator, Panel

from .. import cache, utils
from . import model_browser


class _Job:
    """Hand-off between the operator and its worker thread.

    Only plain Python data crosses this boundary. The worker never touches bpy.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.status = 'Initializing...'
        self.progress = 0
        self.result = None
        self.error = None

    def report(self, status, progress):
        with self.lock:
            self.status = status
            self.progress = progress

    def read(self):
        with self.lock:
            return self.status, self.progress


class _ThreadedOperator(Operator):
    """Runs a worker thread while a modal timer reports its progress.

    Subclasses implement 'work(job)', which runs off the main thread and therefore
    must not touch bpy, and 'apply(context, job)', which runs on the main thread
    once the worker is done.
    """

    _timer = None
    _thread = None
    _job = None
    _last_status = None
    _last_report = 0.0

    TIMER_STEP = 0.1

    def execute(self, context):
        self._job = _Job()
        self._last_status = None
        self._last_report = 0.0

        try:
            payload = self.collect(context)
        except Exception as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}

        if payload is None:
            return {'CANCELLED'}

        self._thread = threading.Thread(target=self._run, args=(payload,), daemon=True)
        self._thread.start()

        window_manager = context.window_manager
        self._timer = window_manager.event_timer_add(self.TIMER_STEP, window=context.window)
        window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _run(self, payload):
        try:
            self._job.result = self.work(self._job, payload)
        except Exception as error:
            self._job.error = str(error)
            import traceback
            traceback.print_exc()

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        import time
        status, progress = self._job.read()
        now = time.time()
        if status and (status != self._last_status or now - self._last_report > 1.0):
            self.report({'INFO'}, f'{status} ({progress}%)')
            self._last_status = status
            self._last_report = now

        if context.area is not None:
            context.area.tag_redraw()

        if not self._thread.is_alive():
            self._finish(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def _finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self._timer = None

        if self._job.error is not None:
            self.report({'ERROR'}, self._job.error)
            return

        self.apply(context, self._job)

    def cancel(self, context):
        # the worker only writes into the cache directory, so it is safe to let it
        # finish on its own, we just stop reporting about it
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        self.report({'INFO'}, 'Cancelled, the cache is still being written in the background')


class TEXTURE_OT_load_files(_ThreadedOperator):
    """Reconnect missing textures from the configured paths and .big archives"""
    bl_idname = 'texture.load_files'
    bl_label = 'Load Files'
    bl_description = 'Reconnect missing textures from the configured paths and .big archives'

    def collect(self, context):
        scene = context.scene

        # find the images that need fixing up front, on the main thread, and work out
        # the name to look them up by here too, since that reads image.filepath
        candidates = []
        for image in bpy.data.images:
            if image.name == 'Render Result':
                continue
            if not image.filepath:
                if os.path.splitext(image.name)[1].lower() in cache.SUPPORTED_EXTENSIONS:
                    candidates.append((image.name, cache.asset_key(image.name)))
                continue
            if not os.path.exists(bpy.path.abspath(image.filepath)):
                # a broken link still names the file it is looking for
                candidates.append((image.name, cache.asset_key(image.filepath)))

        if not candidates:
            self.report({'INFO'}, 'No missing textures found in the current scene')
            return None

        big_paths = utils.selected_big_paths(scene)
        search_paths = utils.search_paths(scene)

        if not big_paths and not search_paths:
            self.report({'ERROR'}, 'No search paths defined')
            return None

        return {'candidates': candidates, 'big_paths': big_paths, 'search_paths': search_paths}

    def work(self, job, payload):
        job.report('Indexing assets...', 20)
        index = cache.asset_index(
            payload['big_paths'], payload['search_paths'],
            cache.SUPPORTED_EXTENSIONS | {'.w3d'},
            progress=lambda done, total: job.report(f'Indexing archives ({done}/{total})...', 20))

        # only the textures actually missing from the scene get resolved, which for
        # a loose file is its own path and for an archive entry extracts just that one
        job.report('Resolving textures...', 70)
        resolved = {}
        for name, key in payload['candidates']:
            path = cache.resolve(index.get(key))
            if path is not None:
                resolved[name] = path

        return {'resolved': resolved, 'candidates': payload['candidates']}

    def apply(self, context, job):
        resolved = job.result['resolved']
        candidates = job.result['candidates']

        fixed = 0
        for name, _ in candidates:
            image = bpy.data.images.get(name)
            path = resolved.get(name)
            if image is None or path is None:
                continue

            image.filepath = path
            image.source = 'FILE'
            try:
                image.reload()
                fixed += 1
            except RuntimeError:
                continue

        if fixed:
            self.report({'INFO'}, f'Fixed {fixed} of {len(candidates)} missing textures')
        else:
            self.report({'WARNING'}, f'Found {len(candidates)} missing textures but could not fix any')


class TEXTURE_OT_clear_cache(Operator):
    """Clear the asset cache and force a re-extraction"""
    bl_idname = 'texture.clear_cache'
    bl_label = 'Clear Cache'
    bl_description = 'Clear the cached files and force a re-extraction on the next run'

    def execute(self, _context):
        cache.clear(
            extra_dirs=(model_browser.PREVIEW_CACHE_DIR,),
            extra_files=(model_browser.PREVIEW_INDEX_FILE,))
        model_browser.invalidate_preview_index()
        model_browser.clear_preview_images()

        self.report({'INFO'}, 'Cache cleared')
        return {'FINISHED'}


class TEXTURE_OT_add_path(Operator):
    bl_idname = 'texture.add_path'
    bl_label = 'Add Search Path'

    def execute(self, context):
        context.scene.texture_search_paths.add()
        return {'FINISHED'}


class TEXTURE_OT_remove_path(Operator):
    bl_idname = 'texture.remove_path'
    bl_label = 'Remove Search Path'

    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.texture_search_paths.remove(self.index)
        return {'FINISHED'}


class TEXTURE_OT_refresh_bigs(Operator):
    bl_idname = 'texture.refresh_bigs'
    bl_label = 'Refresh .big lists'
    bl_description = 'Scan the install paths and populate the .big file lists'

    def execute(self, context):
        utils.refresh_big_lists(context.scene)
        return {'FINISHED'}


class TEXTURE_PT_panel(Panel):
    bl_label = 'Asset search paths'
    bl_idname = 'TEXTURE_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'W3D Tools'

    def draw_big_list(self, layout, scene, enabled_name, show_name, collection_name, label):
        row = layout.row()
        row.prop(scene, enabled_name, text=label)
        expanded = getattr(scene, show_name)
        row.prop(scene, show_name, text='',
                 icon='TRIA_DOWN' if expanded else 'TRIA_RIGHT', emboss=False)

        if not getattr(scene, enabled_name) or not expanded:
            return

        column = layout.column(align=True)
        column.operator('texture.refresh_bigs', text='Refresh .big lists')

        collection = getattr(scene, collection_name)
        if not len(collection):
            column.label(text='No .big files found. Press Refresh.')
            return

        for item in collection:
            column.row(align=True).prop(item, 'selected', text=item.name)

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        self.draw_big_list(layout, scene, 'use_bfme2_assets', 'show_bfme2_bigs',
                           'bfme2_big_files', 'BfMe 2 Assets')
        self.draw_big_list(layout, scene, 'use_rotwk_assets', 'show_rotwk_bigs',
                           'rotwk_big_files', 'BfMe RotWk Assets')

        if scene.use_bfme2_assets or scene.use_rotwk_assets:
            layout.label(text='Extracting .big files may take a while.', icon='INFO')

        layout.separator()

        for index, entry in enumerate(scene.texture_search_paths):
            box = layout.box()
            row = box.row()
            row.prop(entry, 'path', text='')
            row.operator('texture.remove_path', text='', icon='X').index = index

        layout.operator('texture.add_path')

        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator('texture.load_files', icon='FILE_REFRESH')
        row.operator('texture.clear_cache', icon='TRASH', text='Clear Cache')

        big_files, search_files = cache.cache_stats()
        if big_files or search_files:
            box.row().label(
                text=f'Cache: {big_files} .big files, {search_files} search path files', icon='INFO')


CLASSES = (
    TEXTURE_PT_panel,
    TEXTURE_OT_load_files,
    TEXTURE_OT_add_path,
    TEXTURE_OT_remove_path,
    TEXTURE_OT_refresh_bigs,
    TEXTURE_OT_clear_cache)


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)


def unregister():
    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
