# <pep8 compliant>
"""Destroy animation: fractures a structure and tips the pieces to the ground."""

import random

import bpy
from bpy.props import BoolProperty, CollectionProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Matrix, Quaternion, Vector

from .. import utils


class DESTROY_OT_create(Operator):
    bl_idname = 'bfme.destroy_animation'
    bl_label = 'Create Destroy Animation'
    bl_description = 'Create a destroy animation for the selected armature and its children'

    def fracture_and_replace(self, context, obj, armature, split_count, bone_targets):
        """Split obj into split_count pieces, give each piece its own bone."""
        name = obj.name
        parent_bone_name = obj.parent_bone if obj.parent_type == 'BONE' else None
        pieces = []

        try:
            obj.hide_viewport = False
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # centre of mass of the whole object, used as the tipping target
            bpy.ops.object.duplicate()
            probe = context.active_object
            if probe is None or probe == obj:
                raise RuntimeError('failed to duplicate the object')

            bpy.ops.object.select_all(action='DESELECT')
            probe.select_set(True)
            context.view_layer.objects.active = probe
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
            center_of_mass = probe.matrix_world.translation.copy()
            bpy.data.objects.remove(probe, do_unlink=True)

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.duplicate()
            pieces = [context.active_object]
            bpy.ops.object.select_all(action='DESELECT')

            self._bisect_into_pieces(context, pieces, split_count)

            created = []
            for piece in pieces:
                if not len(piece.data.vertices):
                    bpy.data.objects.remove(piece, do_unlink=True)
                    continue

                bpy.ops.object.select_all(action='DESELECT')
                piece.select_set(True)
                context.view_layer.objects.active = piece
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
                piece.select_set(False)

                piece.name = f'{name}_{len(created) + 1:02d}'
                created.append(piece)

            bpy.data.objects.remove(obj, do_unlink=True)

            if not created:
                return

            context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='EDIT')

            armature_matrix_inverse = armature.matrix_world.inverted()
            edit_bones = armature.data.edit_bones

            for piece in created:
                bone = edit_bones.new(piece.name)
                head = armature_matrix_inverse @ piece.matrix_world.translation
                bone.head = head
                # W3D expects the bone rotated 90 degrees onto the Y axis
                bone.tail = head + Vector((0, 1.0, 0.0))

                if parent_bone_name and parent_bone_name in edit_bones:
                    bone.parent = edit_bones[parent_bone_name]

                bone_targets[piece.name] = center_of_mass

            bpy.ops.object.mode_set(mode='OBJECT')

            for piece in created:
                world = piece.matrix_world.copy()
                piece.parent = armature
                piece.parent_type = 'BONE'
                piece.parent_bone = piece.name
                piece.matrix_parent_inverse = Matrix.Identity(4)
                piece.matrix_world = world

            self.report({'INFO'}, f"Fractured '{name}' into {len(created)} pieces.")

        except Exception as error:
            self.report({'ERROR'}, f"Fracturing failed for '{name}': {error}")

    @staticmethod
    def _bisect_into_pieces(context, pieces, split_count):
        """Repeatedly cut the largest piece in half until split_count is reached."""
        guard = split_count * 2

        while len(pieces) < split_count and guard > 0:
            guard -= 1

            # only the largest piece is needed, so pick it instead of sorting the
            # whole list again on every iteration
            target = max(pieces, key=lambda piece: max(piece.dimensions))
            dimensions = target.dimensions

            if dimensions.x >= dimensions.y and dimensions.x >= dimensions.z:
                normal = Vector((1, 0, 0))
            elif dimensions.y >= dimensions.z:
                normal = Vector((0, 1, 0))
            else:
                normal = Vector((0, 0, 1))

            corners = target.bound_box
            center = (Vector(corners[0]) + Vector(corners[6])) / 2.0
            jitter = 0.1 * max(dimensions)
            cut_point = center + Vector((random.uniform(-0.1, 0.1),
                                         random.uniform(-0.1, 0.1),
                                         random.uniform(-0.1, 0.1))) * jitter

            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = target
            target.select_set(True)
            bpy.ops.object.duplicate()
            other = context.active_object

            for obj, clear_inner, clear_outer in ((target, False, True), (other, True, False)):
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.bisect(plane_co=cut_point, plane_no=normal, use_fill=True,
                                    clear_inner=clear_inner, clear_outer=clear_outer)
                bpy.ops.object.mode_set(mode='OBJECT')

            pieces.append(other)

    def execute(self, context):
        scene = context.scene
        armature = scene.destroy_target

        if armature is None:
            self.report({'ERROR'}, 'No target object selected')
            return {'CANCELLED'}

        if armature.type != 'ARMATURE' or not armature.pose:
            self.report({'ERROR'}, 'Target object must be an armature with pose bones.')
            return {'CANCELLED'}

        length = max(1, scene.destroy_length)
        outward_strength = scene.destroy_outward_movement
        down_offset = scene.destroy_downward_offset

        bone_targets = {}

        for item in scene.splitting_object_settings:
            if not item.use_split:
                continue
            child = bpy.data.objects.get(item.name)
            if child is not None and child.parent == armature and child.name in scene.objects:
                self.fracture_and_replace(context, child, armature, item.split_count, bone_targets)

        context.view_layer.update()

        if not armature.animation_data:
            armature.animation_data_create()
        armature.animation_data.action = bpy.data.actions.new(
            name=scene.destroy_name.strip() or 'destroy')

        non_split_bones = set()
        for item in scene.splitting_object_settings:
            if item.use_split:
                continue
            child = bpy.data.objects.get(item.name)
            if child is not None and child.parent == armature and child.parent_type == 'BONE':
                non_split_bones.add(child.parent_bone)

        bone_z_range = self._bone_z_ranges(armature)
        timings = {item.name: (item.start_percent, item.end_percent) for item in scene.destroy_bone_settings}

        original_frame = scene.frame_current
        scene.frame_start = 0
        scene.frame_end = length

        # cleared in one pass for all bones rather than re-walking the action per bone
        utils.clear_bone_fcurves(
            armature.animation_data, (bone.name for bone in armature.pose.bones))

        for pose_bone in armature.pose.bones:
            self._animate_bone(
                scene, armature, pose_bone, length, timings, bone_z_range, bone_targets,
                pose_bone.name in non_split_bones, outward_strength, down_offset)

        scene.frame_set(original_frame)
        self.report({'INFO'}, f'Destroy animation created ({length} frames)')
        return {'FINISHED'}

    @staticmethod
    def _bone_z_ranges(armature):
        """World space Z extent of the meshes attached to each bone."""
        ranges = {}
        for child in armature.children:
            if child.type != 'MESH' or child.parent_type != 'BONE' or not child.parent_bone:
                continue

            matrix = child.matrix_world
            heights = [(matrix @ Vector(corner)).z for corner in child.bound_box]
            low, high = min(heights), max(heights)

            previous = ranges.get(child.parent_bone)
            if previous is None:
                ranges[child.parent_bone] = (low, high)
            else:
                ranges[child.parent_bone] = (min(previous[0], low), max(previous[1], high))
        return ranges

    @staticmethod
    def _animate_bone(scene, armature, pose_bone, length, timings, bone_z_range, bone_targets,
                      is_non_split, outward_strength, down_offset):
        original_location = pose_bone.location.copy()
        rotation_property = 'rotation_quaternion' if pose_bone.rotation_mode == 'QUATERNION' else 'rotation_euler'
        original_rotation = getattr(pose_bone, rotation_property).copy()

        # pose bone translations are applied along the bone's rest axes
        rest_rotation_inverse = (armature.matrix_world @ pose_bone.bone.matrix_local).to_3x3().inverted()
        bone_world = armature.matrix_world @ pose_bone.matrix

        if is_non_split:
            outward = Vector((0, 0, 0))
        else:
            offset = bone_world.translation - armature.matrix_world.translation
            offset.z = 0
            direction = (offset.normalized() if offset.length >= 0.001
                         else Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)).normalized())
            outward = direction * (outward_strength * random.uniform(0.5, 1.5))

        low, high = bone_z_range.get(pose_bone.name, (bone_world.translation.z,) * 2)

        if is_non_split:
            drop = -high - 0.5
            mid_world = Vector((0, 0, drop * 0.5))
            end_world = Vector((0, 0, drop))
            final_rotation = original_rotation
        else:
            median = (low + high) / 2.0
            mid_world = Vector((outward.x, outward.y, -median))
            end_world = Vector((outward.x, outward.y, -median - down_offset))
            final_rotation = DESTROY_OT_create._tipped_rotation(
                pose_bone, bone_world, bone_targets.get(pose_bone.name, Vector((0.0, 0.0, 0.0))),
                original_rotation, rotation_property)

        mid_location = original_location + rest_rotation_inverse @ mid_world
        end_location = original_location + rest_rotation_inverse @ end_world

        start_percent, end_percent = timings.get(pose_bone.name, (None, None))
        if start_percent is None and pose_bone.parent is not None:
            start_percent, end_percent = timings.get(pose_bone.parent.name, (0.0, 100.0))
        if start_percent is None:
            start_percent, end_percent = 0.0, 100.0

        start_frame = int(start_percent / 100.0 * length)
        end_frame = int(end_percent / 100.0 * length)
        mid_frame = start_frame + (end_frame - start_frame) // 2

        def key(location, rotation, frame):
            pose_bone.location = location
            setattr(pose_bone, rotation_property, rotation)
            pose_bone.keyframe_insert(data_path='location', frame=frame)
            pose_bone.keyframe_insert(data_path=rotation_property, frame=frame)

        key(original_location, original_rotation, 0)
        if start_frame > 0:
            key(original_location, original_rotation, start_frame)

        key(mid_location, final_rotation, mid_frame)
        key(end_location, final_rotation, end_frame)
        if end_frame < length:
            key(end_location, final_rotation, length)

    @staticmethod
    def _tipped_rotation(pose_bone, bone_world, target_point, original_rotation, rotation_property):
        """Tip the bone slightly towards the explosion centre."""
        to_target = target_point - bone_world.translation
        axis = Vector((0, 0, 1)).cross(to_target)
        if axis.length < 0.001:
            axis = Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0))
        axis.normalize()

        local_axis = bone_world.to_3x3().inverted() @ axis
        tipping = Quaternion(local_axis, random.uniform(0.1, 0.3))

        if rotation_property == 'rotation_quaternion':
            return original_rotation @ tipping
        return (original_rotation.to_quaternion() @ tipping).to_euler(pose_bone.rotation_mode)


class SplittingObjectSettings(PropertyGroup):
    name: StringProperty(name='Object Name')
    use_split: BoolProperty(name='Split', default=True)
    split_count: IntProperty(name='Pieces', default=4, min=2, max=100,
                             description='Target number of pieces')


class DestroyBoneAnimSettings(PropertyGroup):
    name: StringProperty(name='Bone Name')
    start_percent: FloatProperty(
        name='Start', subtype='PERCENTAGE', default=0.0, min=0.0, max=100.0,
        description="Start of the bone's destruction as a percentage of the total length")
    end_percent: FloatProperty(
        name='End', subtype='PERCENTAGE', default=100.0, min=0.0, max=100.0,
        description="End of the bone's destruction as a percentage of the total length")


SPLIT_COUNT_BY_SIZE = ((25.0, 2), (50.0, 4), (100.0, 8), (200.0, 16))


def update_destroy_settings(_self, context):
    scene = context.scene
    target = scene.destroy_target

    scene.destroy_name = f'{target.name}_d' if target else 'destroy'
    scene.destroy_bone_settings.clear()
    scene.splitting_object_settings.clear()

    if target is None or target.type != 'ARMATURE':
        return

    if target.pose:
        for bone in target.pose.bones:
            scene.destroy_bone_settings.add().name = bone.name

    for child in target.children:
        if child.type != 'MESH':
            continue
        item = scene.splitting_object_settings.add()
        item.name = child.name
        item.use_split = True

        largest = max(child.dimensions)
        item.split_count = next(
            (count for limit, count in SPLIT_COUNT_BY_SIZE if largest < limit), 32)


class DESTROY_PT_panel(Panel):
    bl_label = 'Destroy Animation'
    bl_idname = 'DESTROY_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'W3D Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, 'destroy_target')
        layout.prop(scene, 'destroy_name', text='Anim Name')

        row = layout.row()
        row.prop(scene, 'show_splitting_object_settings', text='Splitting Objects',
                 icon='TRIA_DOWN' if scene.show_splitting_object_settings else 'TRIA_RIGHT', emboss=False)

        if scene.show_splitting_object_settings:
            if not len(scene.splitting_object_settings):
                layout.label(text='No mesh children found.')
            else:
                for item in scene.splitting_object_settings:
                    row = layout.row()
                    row.prop(item, 'use_split', text=item.name)
                    if item.use_split:
                        row.prop(item, 'split_count')

        row = layout.row()
        row.prop(scene, 'show_destroy_bone_settings', text='Per-Bone Timings',
                 icon='TRIA_DOWN' if scene.show_destroy_bone_settings else 'TRIA_RIGHT', emboss=False)

        if scene.show_destroy_bone_settings:
            box = layout.box()
            target = scene.destroy_target
            if not target or target.type != 'ARMATURE':
                box.label(text='Select a target armature to see the bone list.')
            elif not len(scene.destroy_bone_settings):
                box.label(text='Armature has no bones or needs re-selecting.')
            else:
                for item in scene.destroy_bone_settings:
                    row = box.row(align=True)
                    row.label(text=item.name)
                    row.prop(item, 'start_percent', text='')
                    row.prop(item, 'end_percent', text='')

        layout.prop(scene, 'destroy_length', text='Length')
        layout.prop(scene, 'destroy_outward_movement', text='Outwards movement')
        layout.prop(scene, 'destroy_downward_offset', text='Downward movement')

        layout.box().operator('bfme.destroy_animation', text='Create Destroy Animation')


CLASSES = (
    SplittingObjectSettings,
    DestroyBoneAnimSettings,
    DESTROY_PT_panel,
    DESTROY_OT_create)

SCENE_PROPERTIES = (
    'destroy_target',
    'destroy_name',
    'destroy_outward_movement',
    'destroy_downward_offset',
    'destroy_length',
    'destroy_bone_settings',
    'splitting_object_settings',
    'show_destroy_bone_settings',
    'show_splitting_object_settings')


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    scene = bpy.types.Scene
    scene.destroy_target = PointerProperty(
        type=bpy.types.Object,
        name='Target Object',
        description='The armature to destroy',
        poll=lambda self, obj: obj.type == 'ARMATURE',
        update=update_destroy_settings)
    scene.destroy_name = StringProperty(name='Anim Name', description='Name for the new action')
    scene.destroy_outward_movement = FloatProperty(
        name='Outward Movement', default=5.0, min=0.0,
        description='Distance the split pieces move outwards')
    scene.destroy_downward_offset = FloatProperty(
        name='Downward Movement', default=0.0, min=0.0,
        description='Additional distance the split pieces move down')
    scene.destroy_length = IntProperty(name='Length', default=200, min=1)
    scene.destroy_bone_settings = CollectionProperty(type=DestroyBoneAnimSettings)
    scene.splitting_object_settings = CollectionProperty(type=SplittingObjectSettings)
    scene.show_destroy_bone_settings = BoolProperty(name='Show Destroy Settings', default=False)
    scene.show_splitting_object_settings = BoolProperty(name='Show Splitting Settings', default=False)


def unregister():
    for name in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
