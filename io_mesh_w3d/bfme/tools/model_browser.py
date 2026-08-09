# <pep8 compliant>
"""Browse and import .w3d models from the asset cache, with rendered previews."""

import json
import os
import tempfile
import threading
import time

import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList

from .. import cache, utils
from ...common.utils.helpers import set_blend_method
from ...common.utils.material_import import flatten_materials

PREVIEW_CACHE_DIR = os.path.join(tempfile.gettempdir(), 'bfme_w3d_preview')
PREVIEW_INDEX_FILE = os.path.join(tempfile.gettempdir(), 'bfme_w3d_preview_index.json')

PREVIEW_IMAGE_NAME = 'W3D_Preview_Temp'
PREVIEW_RESOLUTION = 256

_preview_index = None


##########################################################################
# preview index
##########################################################################


def load_preview_index():
    global _preview_index

    if _preview_index is not None:
        return _preview_index

    try:
        with open(PREVIEW_INDEX_FILE, 'r') as file:
            _preview_index = json.load(file)
    except (OSError, ValueError):
        _preview_index = {}
    return _preview_index


def save_preview_index(index):
    global _preview_index

    _preview_index = index
    try:
        with open(PREVIEW_INDEX_FILE, 'w') as file:
            json.dump(index, file)
    except OSError:
        pass


def invalidate_preview_index():
    global _preview_index

    _preview_index = None


def reference_signature(reference):
    """Cheap identity of an asset's contents, without materialising it.

    For a loose file that is its own stamp; for an archive entry it is the
    archive's stamp plus the entry's byte range, so a preview can be validated
    without extracting the model first.
    """
    if reference is None:
        return None

    try:
        stat = os.stat(reference[1])
    except OSError:
        return None

    if reference[0] == cache.REF_BIG:
        return [stat.st_mtime, stat.st_size, reference[3], reference[4]]
    return [stat.st_mtime, stat.st_size]


def is_preview_valid(key, reference, preview_path):
    """True when a preview exists and the model has not changed since it was made."""
    if not os.path.exists(preview_path):
        return False

    signature = reference_signature(reference)
    if signature is None:
        return False

    entry = load_preview_index().get(key)
    return entry is not None and entry.get('w3d_signature') == signature


def update_preview_index(key, reference, preview_path):
    signature = reference_signature(reference)
    if signature is None:
        return

    index = load_preview_index()
    index[key] = {
        'w3d_signature': signature,
        'preview_path': preview_path,
        'generated_at': time.time()}
    save_preview_index(index)


def clear_preview_images():
    image = bpy.data.images.get(PREVIEW_IMAGE_NAME)
    if image is not None:
        bpy.data.images.remove(image)


##########################################################################
# model list
##########################################################################


class W3DModelItem(PropertyGroup):
    # the index key rather than a path: a model that lives inside a .big has no path
    # until it is actually needed, at which point it gets materialised on demand
    key: StringProperty(name='Asset Key')
    filename: StringProperty(name='Filename')


def _generate_preview_deferred():
    """Timer callback, so selecting a list entry does not render inside the update."""
    try:
        bpy.ops.w3d.generate_preview()
    except RuntimeError:
        pass
    return None


def on_model_selection_changed(_self, _context):
    # running an operator straight from a property update is not safe, and rendering
    # there would stall every arrow key press through the list, so defer it and let
    # repeated changes collapse into a single run
    if not bpy.app.timers.is_registered(_generate_preview_deferred):
        bpy.app.timers.register(_generate_preview_deferred, first_interval=0.2)


class W3D_UL_model_list(UIList):
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, _index=0, _flt_flag=0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=item.filename, icon='MESH_CUBE')
            row.operator('w3d.import_model', text='', icon='IMPORT', emboss=False).key = item.key
        else:
            layout.alignment = 'CENTER'
            layout.label(text='', icon='MESH_CUBE')

    def filter_items(self, _context, data, propname):
        items = getattr(data, propname)
        # items added by the background auto-refresh are appended, not inserted in
        # order, so the list is sorted for display rather than relying on insertion
        # order
        order = bpy.types.UI_UL_list.sort_items_by_name(items, 'filename')

        if not self.filter_name:
            flags = [self.bitflag_filter_item] * len(items)
        else:
            flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, items, 'filename', reverse=False)
        return flags, order


def _collect_w3d_models(big_paths, search_paths, force_refresh=False):
    """Build the asset index and pick out the .w3d models. No bpy access, worker-thread safe."""
    index = cache.asset_index(big_paths, search_paths, cache.CACHE_EXTENSIONS, force_refresh=force_refresh)
    return sorted(
        (cache.asset_name(reference), key)
        for key, reference in index.items()
        if cache.asset_name(reference).lower().endswith('.w3d'))


class W3D_OT_scan_models(Operator):
    """Scan the asset cache and the .big archives for .w3d models"""
    bl_idname = 'w3d.scan_models'
    bl_label = 'Scan W3D Models'
    bl_description = 'Search for .w3d model files in the configured paths and .big archives'

    _timer = None
    _thread = None
    _models = None
    _pending = None
    _cursor = 0

    BATCH_SIZE = 500

    def execute(self, context):
        scene = context.scene
        scene.w3d_models.clear()

        # drop any auto-refresh batch still being applied, so it does not keep
        # inserting into the list this operator just cleared
        global _auto_refresh_pending_add, _auto_refresh_pending_remove, _auto_refresh_active_key
        _auto_refresh_pending_add = None
        _auto_refresh_pending_remove = None
        _auto_refresh_active_key = None

        # everything the worker needs is read here, on the main thread
        big_paths = utils.selected_big_paths(scene)
        search_paths = utils.search_paths(scene)

        self._pending = []
        self._cursor = 0
        self._models = None

        self._thread = threading.Thread(
            target=self._scan, args=(big_paths, search_paths), daemon=True)
        self._thread.start()

        window_manager = context.window_manager
        self._timer = window_manager.event_timer_add(0.05, window=context.window)
        window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _scan(self, big_paths, search_paths):
        """Worker thread: builds the index, extracts nothing, no bpy access."""
        models = []
        try:
            models = _collect_w3d_models(big_paths, search_paths)
        except Exception as error:
            print(f'[BFME_MODELS] indexing failed: {error}')
        finally:
            self._models = models

    def modal(self, context, event):
        if event.type == 'ESC':
            self._close(context)
            self.report({'INFO'}, 'Cancelled model scan')
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        models = context.scene.w3d_models

        # add in batches so the UI stays responsive, walking an index instead of
        # re-slicing the list, which would copy the remainder on every timer tick
        if self._cursor < len(self._pending):
            end = min(self._cursor + self.BATCH_SIZE, len(self._pending))
            for filename, key in self._pending[self._cursor:end]:
                item = models.add()
                item.filename = filename
                item.key = key
            self._cursor = end

            if context.area is not None:
                context.area.tag_redraw()
            return {'PASS_THROUGH'}

        if self._thread.is_alive():
            return {'PASS_THROUGH'}

        # the index is only ready once the worker is done, hand it over to be listed
        if self._models is not None:
            self._pending = self._models
            self._cursor = 0
            self._models = None
            if self._pending:
                return {'PASS_THROUGH'}

        self._close(context)

        count = len(models)
        if count:
            context.scene.w3d_active_model_index = 0
            self.report({'INFO'}, f'Found {count} .w3d models')
        else:
            self.report({'WARNING'}, 'No .w3d models found. Make sure BfMe assets are selected.')
        return {'FINISHED'}

    def _close(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


##########################################################################
# automatic background refresh
##########################################################################

# while a background scan is running, poll this often for its completion
AUTO_REFRESH_POLL_INTERVAL = 0.5
# once idle, wait this long before starting the next background scan
AUTO_REFRESH_IDLE_INTERVAL = 20.0
# fires the first scan shortly after Blender starts, so the list is populated
# without the user ever pressing 'Scan W3D Models'
AUTO_REFRESH_FIRST_INTERVAL = 1.0
# collection edits are applied this many items at a time, and this often, so a
# first-time scan with thousands of models does not stall Blender for the one
# frame it would take to insert them all at once; matches W3D_OT_scan_models's
# own batch size for the same reason
AUTO_REFRESH_BATCH_SIZE = 500
AUTO_REFRESH_BATCH_INTERVAL = 0.05

_auto_refresh_thread = None
_auto_refresh_result = None
_auto_refresh_pending_add = None
_auto_refresh_pending_remove = None
_auto_refresh_active_key = None


def _auto_refresh_worker(big_paths, search_paths):
    """Worker thread: rebuilds the index and picks out .w3d models, no bpy access.

    Forces a full rebuild instead of trusting the cached signature: a search
    path's own mtime only changes when a direct child is added or removed, not
    when a file further down changes, so the cheap signature check alone would
    miss most real edits. A full rebuild is well under a second even for a full
    install, so redoing it periodically is cheap enough to just always do it.
    """
    global _auto_refresh_result
    try:
        _auto_refresh_result = _collect_w3d_models(big_paths, search_paths, force_refresh=True)
    except Exception as error:
        print(f'[BFME_MODELS] auto refresh failed: {error}')
        _auto_refresh_result = None


def _tag_redraw():
    window_manager = getattr(bpy.context, 'window_manager', None)
    if window_manager is not None:
        for window in window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()


def _begin_apply(scene, models):
    """Diff freshly scanned models against scene.w3d_models and queue the result
    for a batched apply, so the caller's timer tick returns quickly regardless
    of how large the diff is.
    """
    global _auto_refresh_pending_add, _auto_refresh_pending_remove, _auto_refresh_active_key

    items = scene.w3d_models
    existing_keys = {item.key for item in items}
    fresh_filenames = {key: filename for filename, key in models}
    fresh_keys = set(fresh_filenames)

    removed_keys = existing_keys - fresh_keys
    added_keys = fresh_keys - existing_keys
    if not removed_keys and not added_keys:
        return False

    active_item = items[scene.w3d_active_model_index] \
        if 0 <= scene.w3d_active_model_index < len(items) else None
    _auto_refresh_active_key = active_item.key if active_item is not None else None

    _auto_refresh_pending_remove = list(removed_keys)
    _auto_refresh_pending_add = [(key, fresh_filenames[key]) for key in added_keys]
    return True


def _apply_pending_batch():
    """Apply one batch of a diff queued by _begin_apply(). Returns the next delay."""
    global _auto_refresh_pending_add, _auto_refresh_pending_remove, _auto_refresh_active_key

    scene = bpy.context.scene
    if scene is None or not hasattr(scene, 'w3d_models'):
        _auto_refresh_pending_add = None
        _auto_refresh_pending_remove = None
        _auto_refresh_active_key = None
        return AUTO_REFRESH_IDLE_INTERVAL

    items = scene.w3d_models

    if _auto_refresh_pending_remove:
        batch = set(_auto_refresh_pending_remove[:AUTO_REFRESH_BATCH_SIZE])
        # CollectionProperty.remove() is index based, remove from the end so
        # earlier indices stay valid while iterating
        for index in reversed(range(len(items))):
            if items[index].key in batch:
                items.remove(index)
        _auto_refresh_pending_remove = _auto_refresh_pending_remove[AUTO_REFRESH_BATCH_SIZE:]
        _tag_redraw()
        return AUTO_REFRESH_BATCH_INTERVAL

    if _auto_refresh_pending_add:
        batch, _auto_refresh_pending_add = (
            _auto_refresh_pending_add[:AUTO_REFRESH_BATCH_SIZE],
            _auto_refresh_pending_add[AUTO_REFRESH_BATCH_SIZE:])
        for key, filename in batch:
            item = items.add()
            item.filename = filename
            item.key = key
        _tag_redraw()
        if _auto_refresh_pending_add:
            return AUTO_REFRESH_BATCH_INTERVAL

    # both queues are drained now; fix up the active selection once, at the end,
    # rather than after every batch
    _auto_refresh_pending_add = None
    _auto_refresh_pending_remove = None

    if _auto_refresh_active_key is not None:
        for index, item in enumerate(items):
            if item.key == _auto_refresh_active_key:
                if index != scene.w3d_active_model_index:
                    scene.w3d_active_model_index = index
                break
        else:
            scene.w3d_active_model_index = 0  # the old selection is gone
    _auto_refresh_active_key = None

    return AUTO_REFRESH_IDLE_INTERVAL


def _auto_refresh_tick():
    """Registered with bpy.app.timers. Periodically rebuilds the model index in a
    background thread and merges the result in, so the browser stays current
    without the user ever pressing 'Scan W3D Models'.
    """
    global _auto_refresh_thread, _auto_refresh_result
    global _auto_refresh_pending_add, _auto_refresh_pending_remove

    if _auto_refresh_pending_add is not None or _auto_refresh_pending_remove is not None:
        return _apply_pending_batch()

    if _auto_refresh_thread is not None:
        if _auto_refresh_thread.is_alive():
            return AUTO_REFRESH_POLL_INTERVAL

        _auto_refresh_thread = None
        scene = bpy.context.scene
        if _auto_refresh_result is not None and scene is not None and hasattr(scene, 'w3d_models'):
            if _begin_apply(scene, _auto_refresh_result):
                _auto_refresh_result = None
                return AUTO_REFRESH_BATCH_INTERVAL
        _auto_refresh_result = None
        return AUTO_REFRESH_IDLE_INTERVAL

    scene = bpy.context.scene
    if scene is None or not hasattr(scene, 'w3d_models'):
        return AUTO_REFRESH_IDLE_INTERVAL

    big_paths = utils.selected_big_paths(scene)
    search_paths = utils.search_paths(scene)
    if not big_paths and not search_paths:
        return AUTO_REFRESH_IDLE_INTERVAL  # nothing configured yet, nothing to scan

    _auto_refresh_thread = threading.Thread(
        target=_auto_refresh_worker, args=(big_paths, search_paths), daemon=True)
    _auto_refresh_thread.start()
    return AUTO_REFRESH_POLL_INTERVAL


##########################################################################
# preview rendering
##########################################################################


def _configure_preview_scene(scene):
    render = scene.render
    render.resolution_x = PREVIEW_RESOLUTION
    render.resolution_y = PREVIEW_RESOLUTION
    render.film_transparent = True
    render.engine = 'BLENDER_EEVEE'

    eevee = scene.eevee
    # bloom and screen space reflections were removed with EEVEE Next in Blender 4.2
    for name, value in (('use_bloom', False), ('use_ssr', False), ('taa_render_samples', 8)):
        if hasattr(eevee, name):
            setattr(eevee, name, value)

    if scene.world is None:
        scene.world = bpy.data.worlds.new('W3D_Preview_World')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get('Background')
    if background is not None:
        background.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1.0)
        background.inputs['Strength'].default_value = 0.5


def _light_positions(center, size):
    x, y, z = center
    return (
        ((x + size * 2, y, z), 5000 * size, 'front'),
        ((x + size * 1.5, y - size * 1.5, z + size), 4000 * size, 'front_top'),
        ((x - size * 2, y, z), 4000 * size, 'back'),
        ((x - size * 1.5, y + size * 1.5, z + size), 3500 * size, 'back_top'),
        ((x, y + size * 2, z), 4000 * size, 'left'),
        ((x, y - size * 2, z), 4000 * size, 'right'),
        ((x, y, z + size * 2.5), 6000 * size, 'top'),
        ((x + size, y + size, z + size * 2), 3000 * size, 'top_diagonal'),
        ((x, y, z - size), 2000 * size, 'bottom'),
        ((x + size * 1.5, y + size * 1.5, z + size * 0.5), 2500 * size, 'diagonal_1'),
        ((x - size * 1.5, y - size * 1.5, z + size * 0.5), 2500 * size, 'diagonal_2'))


class W3D_OT_generate_preview(Operator):
    """Render a preview thumbnail for the selected model"""
    bl_idname = 'w3d.generate_preview'
    bl_label = 'Generate Preview'

    def execute(self, context):
        scene = context.scene

        if not len(scene.w3d_models):
            return {'CANCELLED'}

        index = scene.w3d_active_model_index
        if not 0 <= index < len(scene.w3d_models):
            return {'CANCELLED'}

        item = scene.w3d_models[index]
        preview_path = os.path.join(PREVIEW_CACHE_DIR, f'w3d_preview_{item.filename}.png')
        reference = cache.cached_asset_index().get(item.key)

        # checked against the reference, so a cached preview costs no extraction
        if is_preview_valid(item.key, reference, preview_path):
            if self._show(context, preview_path):
                return {'FINISHED'}
        elif os.path.exists(preview_path):
            try:
                os.remove(preview_path)
            except OSError:
                pass

        # the model's skeleton and textures come along, the importer looks them up
        # by name next to the file it is given
        filepath = cache.stage_for_import(cache.cached_asset_index(), item.key)
        if filepath is None:
            self.report({'WARNING'}, f'Could not read {item.filename}')
            return {'CANCELLED'}

        self._render(context, item.key, reference, filepath, preview_path)
        return {'FINISHED'}

    def _show(self, context, preview_path):
        clear_preview_images()
        try:
            image = bpy.data.images.load(preview_path, check_existing=False)
        except RuntimeError as error:
            print(f'[BFME_PREVIEW] could not load cached preview: {error}')
            return False

        image.name = PREVIEW_IMAGE_NAME
        image.preview_ensure()
        context.scene.w3d_preview_image = image.name

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
        return True

    def _render(self, context, key, reference, filepath, preview_path):
        scene = context.scene
        scene.w3d_preview_generating = True

        try:
            os.makedirs(PREVIEW_CACHE_DIR, exist_ok=True)
        except OSError:
            pass

        original_frame = scene.frame_current

        objects_before = set(bpy.data.objects)
        collections_before = set(bpy.data.collections)
        meshes_before = set(bpy.data.meshes)
        armatures_before = set(bpy.data.armatures)
        materials_before = set(bpy.data.materials)

        preview_scene = None
        new_objects = []
        light_data = []
        camera_data = None

        try:
            result = utils.import_w3d(filepath)
            if 'FINISHED' not in result:
                return

            new_objects = list(set(bpy.data.objects) - objects_before)
            if not new_objects:
                return

            # animated models look best at the end of their animation
            last = max((frame for frame in (utils.last_keyframe(obj) for obj in new_objects)
                        if frame is not None), default=None)
            if last is not None and last > scene.frame_current:
                scene.frame_set(int(last))
                context.view_layer.update()

            # the specular fix already happened inside import_w3d() above; only the
            # forced alpha blending is specific to rendering a preview thumbnail
            for material in flatten_materials(new_objects):
                set_blend_method(material, 'BLEND')

            # untextured meshes only carry a flat diffuse colour, they add nothing
            for obj in new_objects:
                if obj.type != 'MESH' or not obj.data.materials:
                    continue
                obj.hide_render = not any(
                    node.type == 'TEX_IMAGE' and node.image
                    for material in obj.data.materials if material is not None and material.node_tree
                    for node in material.node_tree.nodes)

            preview_scene = bpy.data.scenes.new('W3D_Preview_Scene')
            _configure_preview_scene(preview_scene)
            preview_scene.frame_set(scene.frame_current)

            for obj in new_objects:
                for collection in list(obj.users_collection):
                    collection.objects.unlink(obj)
                preview_scene.collection.objects.link(obj)

            camera_data = bpy.data.cameras.new('W3D_Preview_Camera')
            camera = bpy.data.objects.new('W3D_Preview_Camera', camera_data)
            preview_scene.collection.objects.link(camera)
            preview_scene.camera = camera

            visible = [obj for obj in new_objects if not obj.hide_render]
            if visible:
                minimum, maximum = utils.world_bounds(visible)
                if minimum is None:
                    return

                center = (minimum + maximum) / 2
                size = max(maximum[i] - minimum[i] for i in range(3)) or 1.0

                camera.location = (center.x + size * 1.5, center.y - size * 1.5, center.z + size * 0.8)
                camera.rotation_euler = (1.1, 0, 0.785)

                for position, energy, suffix in _light_positions(center, size):
                    data = bpy.data.lights.new(f'W3D_Preview_Light_{suffix}', 'POINT')
                    data.energy = energy
                    data.shadow_soft_size = size * 0.3
                    data.use_shadow = False
                    light_data.append(data)

                    light = bpy.data.objects.new(f'W3D_Preview_Light_{suffix}', data)
                    preview_scene.collection.objects.link(light)
                    light.location = position

            preview_scene.render.filepath = preview_path
            # rendering the scene by name avoids swapping the window's scene, which
            # would leave the window pointing at a removed scene if this raises
            bpy.ops.render.render(write_still=True, scene=preview_scene.name)

            if os.path.exists(preview_path):
                self._show(context, preview_path)
                update_preview_index(key, reference, preview_path)

        except Exception as error:
            print(f'[BFME_PREVIEW] preview generation failed: {error}')
            import traceback
            traceback.print_exc()
            scene.w3d_preview_image = ''
        finally:
            self._cleanup(preview_scene, new_objects, camera_data, light_data,
                          collections_before, meshes_before, armatures_before, materials_before)
            scene.frame_set(original_frame)
            scene.w3d_preview_generating = False

    @staticmethod
    def _cleanup(preview_scene, new_objects, camera_data, light_data,
                 collections_before, meshes_before, armatures_before, materials_before):
        """Remove everything the preview created, in dependency order."""
        if preview_scene is not None:
            bpy.data.scenes.remove(preview_scene)

        for obj in new_objects:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except ReferenceError:
                continue

        if camera_data is not None:
            bpy.data.cameras.remove(camera_data)

        for data in light_data:
            try:
                bpy.data.lights.remove(data)
            except ReferenceError:
                continue

        world = bpy.data.worlds.get('W3D_Preview_World')
        if world is not None:
            bpy.data.worlds.remove(world)

        for collection in set(bpy.data.collections) - collections_before:
            bpy.data.collections.remove(collection)
        for mesh in set(bpy.data.meshes) - meshes_before:
            bpy.data.meshes.remove(mesh)
        for armature in set(bpy.data.armatures) - armatures_before:
            bpy.data.armatures.remove(armature)
        for material in set(bpy.data.materials) - materials_before:
            bpy.data.materials.remove(material)


class W3D_OT_import_model(Operator):
    """Import the selected W3D model"""
    bl_idname = 'w3d.import_model'
    bl_label = 'Import W3D Model'
    bl_description = 'Import this W3D model'

    key: StringProperty()

    def execute(self, _context):
        # the model and its skeleton and textures get written out at this point,
        # rather than the whole archive
        filepath = cache.stage_for_import(cache.cached_asset_index(), self.key)
        if filepath is None:
            self.report({'ERROR'}, f"Could not read '{self.key}'. Re-scan the models.")
            return {'CANCELLED'}

        try:
            # the specular fix runs inside the core import operator itself, so it
            # applies here exactly as it does for File > Import
            result = utils.import_w3d(filepath)
        except RuntimeError as error:
            self.report({'ERROR'}, f'Import failed: {error}')
            return {'CANCELLED'}

        if 'FINISHED' not in result:
            self.report({'ERROR'}, f'Import failed for {os.path.basename(filepath)}')
            return {'CANCELLED'}

        self.report({'INFO'}, f'Imported {os.path.basename(filepath)}')
        return {'FINISHED'}


class W3D_IMPORTER_PT_panel(Panel):
    bl_label = 'W3D Model Browser'
    bl_idname = 'W3D_IMPORTER_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'W3D Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text='Browse .w3d models from BIG archives', icon='INFO')
        layout.operator('w3d.scan_models', icon='FILE_REFRESH')

        if not len(scene.w3d_models):
            layout.separator()
            box = layout.box()
            box.label(text='No models found in cache.', icon='ERROR')
            box.label(text="1. Enable BfMe assets in 'Asset search paths'")
            box.label(text='2. Select .big files containing models')
            box.label(text="3. Click 'Scan W3D Models'")
            return

        layout.separator()
        layout.label(text=f'Total: {len(scene.w3d_models)} models', icon='MESH_DATA')

        layout.row().template_list(
            'W3D_UL_model_list', '', scene, 'w3d_models', scene, 'w3d_active_model_index', rows=10)

        layout.separator()
        box = layout.box()
        column = box.column(align=True)
        column.row().label(text='Preview', icon='RESTRICT_RENDER_OFF')

        if scene.w3d_preview_generating:
            column.row().label(text='Generating preview...', icon='TIME')
            return

        image = bpy.data.images.get(scene.w3d_preview_image)
        if image is None:
            column.label(text='Select a model to preview', icon='INFO')
            return

        column.template_icon(icon_value=image.preview.icon_id, scale=8.0)


CLASSES = (
    W3DModelItem,
    W3D_UL_model_list,
    W3D_OT_scan_models,
    W3D_OT_generate_preview,
    W3D_OT_import_model,
    W3D_IMPORTER_PT_panel)


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    scene = bpy.types.Scene
    scene.w3d_models = CollectionProperty(type=W3DModelItem)
    scene.w3d_active_model_index = IntProperty(
        name='Active Model Index', default=0, update=on_model_selection_changed)
    scene.w3d_preview_image = StringProperty(default='')
    scene.w3d_preview_generating = BoolProperty(default=False)

    # persistent so the auto-refresh survives switching to a different .blend file,
    # not just a fresh Blender start
    if not bpy.app.timers.is_registered(_auto_refresh_tick):
        bpy.app.timers.register(_auto_refresh_tick, first_interval=AUTO_REFRESH_FIRST_INTERVAL, persistent=True)


def unregister():
    global _auto_refresh_thread, _auto_refresh_result
    global _auto_refresh_pending_add, _auto_refresh_pending_remove, _auto_refresh_active_key

    if bpy.app.timers.is_registered(_auto_refresh_tick):
        bpy.app.timers.unregister(_auto_refresh_tick)
    _auto_refresh_thread = None
    _auto_refresh_result = None
    _auto_refresh_pending_add = None
    _auto_refresh_pending_remove = None
    _auto_refresh_active_key = None

    if bpy.app.timers.is_registered(_generate_preview_deferred):
        bpy.app.timers.unregister(_generate_preview_deferred)

    for name in ('w3d_models', 'w3d_active_model_index', 'w3d_preview_image', 'w3d_preview_generating'):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
