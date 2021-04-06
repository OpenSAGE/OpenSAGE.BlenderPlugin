# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.w3d.adaptive_delta import decode
from io_mesh_w3d.common.structs.animation import *
from io_mesh_w3d.w3d.structs.compressed_animation import *


def is_roottransform(channel):
    return channel.pivot == 0


def is_translation(channel):
    return channel.type < 3


def is_visibility(channel):
    return isinstance(channel, AnimationBitChannel) or channel.type == CHANNEL_VIS


def get_bone(context, rig, hierarchy, channel):
    if is_roottransform(channel):
        if is_visibility(channel):
            context.warning(
                f'armature \'{hierarchy.name()}\' might have been hidden due to visibility animation channels!')
        return rig

    if channel.pivot >= len(hierarchy.pivots):
        context.warning(
            f'animation channel for bone with ID \'{channel.pivot}\' is invalid -> armature has only {len(hierarchy.pivots)} bones!')
        return None
    pivot = hierarchy.pivots[channel.pivot]

    if is_visibility(channel) and pivot.name in rig.data.bones:
        return rig.data.bones[pivot.name]
    return rig.pose.bones[pivot.name]


def setup_animation(animation):
    bpy.context.scene.render.fps = animation.header.frame_rate
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = animation.header.num_frames - 1


creation_options = {'INSERTKEY_NEEDED'}


def set_translation(bone, index, frame, value):
    bone.location[index] = value
    bone.keyframe_insert(data_path='location', index=index, frame=frame, options=creation_options)


def set_rotation(bone, frame, value):
    bone.rotation_quaternion = value
    bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)


def set_visibility(bone, frame, value):
    if isinstance(bone, bpy.types.Bone):
        bone.visibility = value
        bone.keyframe_insert(data_path='visibility', frame=frame, options=creation_options)
    else:
        bone.hide_viewport = bool(value)
        bone.keyframe_insert(data_path='hide_viewport', frame=frame, options=creation_options)


def set_keyframe(bone, channel, frame, value):
    if is_visibility(channel):
        set_visibility(bone, frame, value)
    elif is_translation(channel):
        set_translation(bone, channel.type, frame, value)
    else:
        set_rotation(bone, frame, value)


def apply_timecoded(bone, channel):
    for key in channel.time_codes:
        set_keyframe(bone, channel, key.time_code, key.value)


def apply_motion_channel_time_coded(bone, channel):
    for dat in channel.data:
        set_keyframe(bone, channel, dat.time_code, dat.value)


def apply_adaptive_delta(bone, channel):
    data = decode(channel)
    for i in range(channel.num_time_codes):
        set_keyframe(bone, channel, i, data[i])


def apply_uncompressed(bone, channel):
    for index in range(channel.last_frame - channel.first_frame + 1):
        data = channel.data[index]
        frame = index + channel.first_frame
        set_keyframe(bone, channel, frame, data)


def process_channels(context, hierarchy, channels, rig, apply_func):
    for channel in channels:
        obj = get_bone(context, rig, hierarchy, channel)
        if obj is None:
            continue

        apply_func(obj, channel)


def process_motion_channels(context, hierarchy, channels, rig):
    for channel in channels:
        obj = get_bone(context, rig, hierarchy, channel)
        if obj is None:
            continue

        if channel.delta_type == 0:
            apply_motion_channel_time_coded(obj, channel)
        else:
            apply_adaptive_delta(obj, channel)


def create_animation(context, rig, animation, hierarchy):
    if animation is None:
        return

    setup_animation(animation)

    if isinstance(animation, CompressedAnimation):
        process_channels(context, hierarchy, animation.time_coded_channels, rig, apply_timecoded)
        process_channels(context, hierarchy, animation.adaptive_delta_channels, rig, apply_adaptive_delta)
        process_motion_channels(context, hierarchy, animation.motion_channels, rig)
    else:
        process_channels(context, hierarchy, animation.channels, rig, apply_uncompressed)

    bpy.context.scene.frame_set(0)
