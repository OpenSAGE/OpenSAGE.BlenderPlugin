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
        if not self.filter_name:
            return [self.bitflag_filter_item] * len(items), []

        flags = bpy.types.UI_UL_list.filter_items_by_name(
            self.filter_name, self.bitflag_filter_item, items, 'filename', reverse=False)
        return flags, []


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
            index = cache.asset_index(big_paths, search_paths, cache.CACHE_EXTENSIONS)
            models = sorted(
                (cache.asset_name(reference), key)
                for key, reference in index.items()
                if cache.asset_name(reference).lower().endswith('.w3d'))
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
# preview rendering
##########################################################################


def _flatten_materials(objects):
    """Every unique material used by the objects and their children, without recursion.

    'Object.children' walks all objects in the file on every access, so recursing
    over it is quadratic. 'children_recursive' resolves the whole subtree in one go.
    """
    seen = set()
    materials = []

    for root in objects:
        for obj in (root, *root.children_recursive):
            if obj.type != 'MESH' or obj.data is None:
                continue
            for material in obj.data.materials:
                if material is not None and material.name not in seen:
                    seen.add(material.name)
                    materials.append(material)
    return materials


def _flatten_principled_specular(materials):
    """Kill the specular highlight, W3D models are authored without one."""
    for material in materials:
        node_tree = material.node_tree
        if node_tree is None:
            continue
        for node in node_tree.nodes:
            if node.type != 'BSDF_PRINCIPLED':
                continue
            for input_name in ('Specular IOR Level', 'IOR Level', 'Specular'):
                socket = node.inputs.get(input_name)
                if socket is not None:
                    socket.default_value = 0.0
                    break


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

            materials = _flatten_materials(new_objects)
            for material in materials:
                set_blend_method(material, 'BLEND')
            _flatten_principled_specular(materials)

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

        objects_before = {obj.name for obj in bpy.data.objects}

        try:
            result = utils.import_w3d(filepath)
        except RuntimeError as error:
            self.report({'ERROR'}, f'Import failed: {error}')
            return {'CANCELLED'}

        if 'FINISHED' not in result:
            self.report({'ERROR'}, f'Import failed for {os.path.basename(filepath)}')
            return {'CANCELLED'}

        imported = [obj for obj in bpy.data.objects if obj.name not in objects_before]
        _flatten_principled_specular(_flatten_materials(imported))

        self.report({'INFO'}, f'Imported {os.path.basename(filepath)}')
        return {'FINISHED'}


class W3D_IMPORTER_PT_panel(Panel):
    bl_label = 'W3D Model Browser'
    bl_idname = 'W3D_IMPORTER_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'W3D Tools'

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


def unregister():
    if bpy.app.timers.is_registered(_generate_preview_deferred):
        bpy.app.timers.unregister(_generate_preview_deferred)

    for name in ('w3d_models', 'w3d_active_model_index', 'w3d_preview_image', 'w3d_preview_generating'):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
