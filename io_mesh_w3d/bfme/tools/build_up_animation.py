# <pep8 compliant>
"""Build-up animation: raises the bones of a structure into place over time."""

import bpy
from bpy.props import BoolProperty, CollectionProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector

from .. import utils


class BUILDUP_OT_create(Operator):
    bl_idname = 'bfme.build_up_animation'
    bl_label = 'Create Build-up Animation'
    bl_description = 'Create a build-up animation for the selected armature'

    def execute(self, context):
        scene = context.scene
        target = scene.build_up_target

        if target is None:
            self.report({'ERROR'}, 'No target object selected')
            return {'CANCELLED'}

        if target.type != 'ARMATURE' or not target.pose:
            self.report({'ERROR'}, 'Target object must be an armature with pose bones.')
            return {'CANCELLED'}

        length = max(1, scene.build_up_length)

        highest = utils.max_world_vertex_z(bpy.data.objects)
        if highest is None:
            highest = max((obj.matrix_world.to_translation().z for obj in bpy.data.objects), default=None)
        if highest is None:
            self.report({'ERROR'}, 'Could not determine scene height')
            return {'CANCELLED'}

        shift = highest + 0.001

        if not target.animation_data:
            target.animation_data_create()
        target.animation_data.action = bpy.data.actions.new(name=scene.build_up_name.strip() or 'build_up')

        # one dict lookup per bone instead of a linear scan through the settings
        timings = {item.name: (item.start_percent, item.end_percent) for item in scene.bone_anim_settings}

        original_frame = scene.frame_current
        scene.frame_start = 0
        scene.frame_end = length

        utils.clear_bone_fcurves(
            target.animation_data, (bone.name for bone in target.pose.bones), properties=('location',))

        for pose_bone in target.pose.bones:
            original_location = pose_bone.location.copy()

            # pose bone locations are expressed in the bone's own rest space
            rotation = (target.matrix_world @ pose_bone.matrix).to_3x3().inverted()
            down = original_location + rotation @ Vector((0, 0, -shift))

            start_percent, end_percent = timings.get(pose_bone.name, (0.0, 100.0))
            start_frame = int(start_percent / 100.0 * length)
            end_frame = int(end_percent / 100.0 * length)

            pose_bone.location = down
            pose_bone.keyframe_insert(data_path='location', frame=0)
            if start_frame > 0:
                pose_bone.keyframe_insert(data_path='location', frame=start_frame)

            pose_bone.location = original_location
            pose_bone.keyframe_insert(data_path='location', frame=end_frame)
            if end_frame < length:
                pose_bone.keyframe_insert(data_path='location', frame=length)

        scene.frame_set(original_frame)
        self.report({'INFO'}, f'Build-up animation created ({length} frames), bones shifted by {shift:.3f}')
        return {'FINISHED'}


class BoneAnimSettings(PropertyGroup):
    name: StringProperty(name='Bone Name')
    start_percent: FloatProperty(
        name='Start', subtype='PERCENTAGE', default=0.0, min=0.0, max=100.0,
        description="Start of the bone's build-up as a percentage of the total length")
    end_percent: FloatProperty(
        name='End', subtype='PERCENTAGE', default=100.0, min=0.0, max=100.0,
        description="End of the bone's build-up as a percentage of the total length")


def update_bone_list(_self, context):
    scene = context.scene
    target = scene.build_up_target

    scene.build_up_name = f'{target.name}_a' if target else 'build_up'
    scene.bone_anim_settings.clear()

    if target and target.type == 'ARMATURE' and target.pose:
        for bone in target.pose.bones:
            scene.bone_anim_settings.add().name = bone.name


class BUILDUP_PT_panel(Panel):
    bl_label = 'Build-up Animation'
    bl_idname = 'BUILDUP_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'SCENE_PT_bfme'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, 'build_up_target')
        layout.prop(scene, 'build_up_name', text='Anim Name')

        row = layout.row()
        row.prop(scene, 'show_bone_settings', text='Per-Bone Timings',
                 icon='TRIA_DOWN' if scene.show_bone_settings else 'TRIA_RIGHT', emboss=False)

        if scene.show_bone_settings:
            box = layout.box()
            target = scene.build_up_target
            if not target or target.type != 'ARMATURE':
                box.label(text='Select a target armature to see the bone list.')
            elif not len(scene.bone_anim_settings):
                box.label(text='Armature has no bones or needs re-selecting.')
            else:
                for item in scene.bone_anim_settings:
                    row = box.row(align=True)
                    row.label(text=item.name)
                    row.prop(item, 'start_percent', text='')
                    row.prop(item, 'end_percent', text='')

        layout.prop(scene, 'build_up_length', text='Length')
        layout.box().operator('bfme.build_up_animation', text='Create Build-up Animation')


CLASSES = (
    BoneAnimSettings,
    BUILDUP_PT_panel,
    BUILDUP_OT_create)

SCENE_PROPERTIES = (
    'build_up_target',
    'build_up_name',
    'build_up_length',
    'bone_anim_settings',
    'show_bone_settings')


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    scene = bpy.types.Scene
    scene.build_up_target = PointerProperty(
        type=bpy.types.Object,
        name='Target Object',
        description='The armature to build up',
        poll=lambda self, obj: obj.type == 'ARMATURE',
        update=update_bone_list)
    scene.build_up_name = StringProperty(name='Anim Name', description='Name for the new action', default='')
    scene.build_up_length = IntProperty(name='Length', default=500, min=1)
    scene.bone_anim_settings = CollectionProperty(type=BoneAnimSettings)
    scene.show_bone_settings = BoolProperty(name='Show Bone Settings', default=False)


def unregister():
    for name in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
