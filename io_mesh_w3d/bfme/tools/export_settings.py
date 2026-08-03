# <pep8 compliant>
"""A simplified export front-end for the W3D exporter."""

import os
import re

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

BLENDER_SUFFIX = re.compile(r'\.\d{3}$')

FILE_FORMATS = {'W3D': '.w3d', 'W3X': '.w3x'}

MODE_LABELS = {
    'HM': 'Hierarchical Model',
    'HAM': 'Hierarchical Animated Model',
    'H': 'Skeleton',
    'A': 'Animation'}


class BFME_ExportSettings(PropertyGroup):
    export_name: StringProperty(
        name='Name', description='Name of the exported file or animation', default='')
    export_path: StringProperty(
        name='Path', description='Directory to export to', default='', subtype='DIR_PATH')
    file_format: EnumProperty(
        name='Format',
        items=[('W3D', 'Westwood 3D Binary', 'Binary .w3d, used by the BfMe games'),
               ('W3X', 'Westwood 3D XML', 'XML .w3x, used by later SAGE games')],
        default='W3D')
    mode: EnumProperty(
        name='Mode',
        items=[('HM', 'Hierarchical Model', 'Static model'),
               ('HAM', 'Hierarchical Animated Model', 'Animated model'),
               ('H', 'Skeleton', 'Skeleton only'),
               ('A', 'Animation', 'Animation only')],
        default='HM')
    use_existing_skeleton: BoolProperty(
        name='Use Existing Skeleton',
        description='Reference an existing skeleton instead of exporting a new one',
        default=False)
    force_vertex_materials: BoolProperty(
        name='Force Vertex Materials',
        description='Export all materials as vertex materials',
        default=False)


class BFME_OT_auto_configure_export(Operator):
    bl_idname = 'bfme.auto_configure_export'
    bl_label = 'Auto-Detect Settings'
    bl_description = 'Detect the export settings from the scene'

    def execute(self, context):
        settings = context.scene.bfme_export_settings
        obj = context.active_object

        has_animation = bool(obj and obj.animation_data and obj.animation_data.action)

        if has_animation:
            settings.export_name = obj.animation_data.action.name
        elif obj is not None and obj.users_collection:
            settings.export_name = obj.users_collection[0].name

        settings.export_path = self._detect_path(context, obj)
        settings.file_format = 'W3D'
        settings.mode = 'HAM' if has_animation else 'HM'
        settings.use_existing_skeleton = has_animation
        settings.force_vertex_materials = False

        self.report({'INFO'}, 'Export settings auto-detected')
        return {'FINISHED'}

    @staticmethod
    def _detect_path(context, obj):
        for source in (context.scene.get('bfme_last_import_path'),
                       obj.get('bfme_import_path') if obj is not None else None):
            if source and os.path.isdir(source):
                return source

        if bpy.data.is_saved:
            return os.path.dirname(bpy.data.filepath)
        return ''


class BFME_OT_export_model(Operator):
    bl_idname = 'bfme.export_model'
    bl_label = 'Export'
    bl_description = 'Export the model with the W3D exporter'

    def execute(self, context):
        settings = context.scene.bfme_export_settings

        if not settings.export_path:
            self.report({'ERROR'}, 'Export path is not set')
            return {'CANCELLED'}
        if not settings.export_name:
            self.report({'ERROR'}, 'Export name is not set')
            return {'CANCELLED'}

        fixed = self.reparent_bone_meshes(context)
        if fixed:
            self.report({'INFO'}, f'Auto-fixed {fixed} mesh/bone conflict(s)')

        self.clean_texture_names()

        directory = bpy.path.abspath(settings.export_path)
        filepath = os.path.join(directory, settings.export_name + FILE_FORMATS[settings.file_format])

        try:
            result = bpy.ops.export_mesh.westwood_w3d(
                filepath=filepath,
                file_format=settings.file_format,
                export_mode=settings.mode,
                use_existing_skeleton=settings.use_existing_skeleton,
                force_vertex_materials=settings.force_vertex_materials)
        except RuntimeError as error:
            self.report({'ERROR'}, f'Export failed: {error}')
            return {'CANCELLED'}

        if 'FINISHED' not in result:
            self.report({'ERROR'}, 'Export failed')
            return {'CANCELLED'}

        if settings.file_format == 'W3D' and os.path.exists(filepath):
            self.replace_texture_extensions(filepath)

        label = MODE_LABELS.get(settings.mode, settings.mode)
        self.report({'INFO'}, f"Exported '{settings.export_name}' as {label}")
        return {'FINISHED'}

    @staticmethod
    def reparent_bone_meshes(context):
        """Bone parent meshes that share a name with a bone but are neither skinned nor parented."""
        armature = next((obj for obj in context.scene.objects
                         if obj.type == 'ARMATURE' and not obj.hide_viewport), None)
        if armature is None:
            return 0

        bone_names = {bone.name for bone in armature.data.bones}
        fixed = 0

        for obj in context.scene.objects:
            if obj.type != 'MESH' or obj.hide_viewport or obj.name not in bone_names:
                continue

            is_skinned = len(obj.vertex_groups) > 0
            is_bone_parented = (obj.parent == armature
                                and obj.parent_type == 'BONE'
                                and obj.parent_bone == obj.name)

            if not is_skinned and not is_bone_parented:
                obj.parent = armature
                obj.parent_type = 'BONE'
                obj.parent_bone = obj.name
                fixed += 1

        return fixed

    @staticmethod
    def clean_texture_names():
        """Drop Blender's .001 suffixes so the exported texture names stay correct."""
        count = 0
        for image in list(bpy.data.images):
            if not BLENDER_SUFFIX.search(image.name):
                continue

            clean_name = BLENDER_SUFFIX.sub('', image.name)
            existing = bpy.data.images.get(clean_name)

            if existing is not None and existing != image:
                image.user_remap(existing)
                count += 1
            elif existing is None:
                image.name = clean_name
                count += 1

        if count:
            print(f'[BFME_EXPORT] cleaned up {count} texture names')

    @staticmethod
    def replace_texture_extensions(filepath):
        """Point the exported texture references at .tga, which is what the games ship."""
        try:
            with open(filepath, 'rb') as file:
                data = file.read()
        except OSError as error:
            print(f'[BFME_EXPORT] could not read {filepath}: {error}')
            return

        original = data
        # one linear pass per casing instead of re-scanning the whole file per hit
        for old, new in ((b'.dds', b'.tga'), (b'.DDS', b'.TGA'), (b'.Dds', b'.Tga')):
            data = data.replace(old, new)

        if data == original:
            return

        try:
            with open(filepath, 'wb') as file:
                file.write(data)
        except OSError as error:
            print(f'[BFME_EXPORT] could not write {filepath}: {error}')


class BFME_PT_export_settings(Panel):
    bl_label = 'Export Settings'
    bl_idname = 'BFME_PT_export_settings'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_parent_id = 'SCENE_PT_bfme'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bfme_export_settings

        layout.operator('bfme.auto_configure_export', icon='FILE_REFRESH')
        layout.prop(settings, 'export_name')
        layout.prop(settings, 'export_path')
        layout.prop(settings, 'file_format')
        layout.prop(settings, 'mode')
        layout.prop(settings, 'use_existing_skeleton')
        layout.prop(settings, 'force_vertex_materials')

        layout.separator()
        layout.operator('bfme.export_model', icon='EXPORT')


CLASSES = (
    BFME_ExportSettings,
    BFME_OT_auto_configure_export,
    BFME_OT_export_model,
    BFME_PT_export_settings)


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)
    bpy.types.Scene.bfme_export_settings = PointerProperty(type=BFME_ExportSettings)


def unregister():
    if hasattr(bpy.types.Scene, 'bfme_export_settings'):
        del bpy.types.Scene.bfme_export_settings

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
