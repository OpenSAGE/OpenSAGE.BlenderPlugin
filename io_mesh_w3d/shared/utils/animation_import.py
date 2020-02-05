# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.w3d.adaptive_delta import decode
from io_mesh_w3d.shared.structs.animation import *


def is_roottransform(channel):
    return channel.pivot == 0


def is_translation(channel):
    return channel.type < 3


def is_rotation(channel):
    return channel.type == 6


def is_visibility(channel):
    return isinstance(channel, AnimationBitChannel)


def get_bone(context, rig, hierarchy, channel):
    if is_roottransform(channel):
        return rig

    pivot = hierarchy.pivots[channel.pivot]

    if rig is not None:
        if is_visibility(channel) and pivot.name in rig.data.bones:
            return rig.data.bones[pivot.name]
        elif pivot.name in rig.pose.bones:
            return rig.pose.bones[pivot.name]
    return bpy.data.objects[pivot.name]


def setup_animation(animation):
    bpy.context.scene.render.fps = animation.header.frame_rate
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = animation.header.num_frames - 1


creation_options = {'INSERTKEY_NEEDED'}


def set_translation(bone, index, frame, value):
    bone.location[index] = value
    bone.keyframe_insert(data_path='location', index=index,
                         frame=frame, options=creation_options)


def set_rotation(bone, frame, value):
    bone.rotation_quaternion = value
    bone.keyframe_insert(data_path='rotation_quaternion',
                         frame=frame)


def set_visibility(bone, frame, value):
    if isinstance(bone, bpy.types.Bone):
        bone.hide = value
        bone.keyframe_insert(data_path='hide', frame=frame, options=creation_options)
    else:
        bone.hide_viewport = value
        bone.keyframe_insert(data_path='hide_viewport',
                             frame=frame, options=creation_options)


def set_keyframe(bone, channel, frame, value):
    if is_visibility(channel):
        set_visibility(bone, frame, value)
    elif is_translation(channel):
        set_translation(bone, channel.type, frame, value)
    elif is_rotation(channel):
        set_rotation(bone, frame, value)


def apply_timecoded(bone, channel, _):
    for key in channel.time_codes:
        set_keyframe(bone, channel, key.time_code, key.value)


def apply_motion_channel_time_coded(bone, channel):
    for dat in channel.data:
        set_keyframe(bone, channel, dat.time_code, dat.value)


def apply_adaptive_delta(bone, channel):
    data = decode(channel)
    for i in range(channel.num_time_codes):
        set_keyframe(bone, channel, i, data[i])


def apply_uncompressed(bone, channel, hierarchy):
    for index in range(channel.last_frame - channel.first_frame + 1):
        data = channel.data[index]
        frame = index + channel.first_frame
        set_keyframe(bone, channel, frame, data)


def process_channels(context, hierarchy, channels, rig, apply_func):
    for channel in channels:
        obj = get_bone(context, rig, hierarchy, channel)

        apply_func(obj, channel, hierarchy)


def process_motion_channels(context, hierarchy, channels, rig):
    for channel in channels:
        obj = get_bone(context, rig, hierarchy, channel)

        if channel.delta_type == 0:
            apply_motion_channel_time_coded(obj, channel)
        else:
            apply_adaptive_delta(obj, channel)


def create_animation(context, rig, animation, hierarchy, compressed=False):
    if animation is None:
        return

    setup_animation(animation)

    if not compressed:
        process_channels(context, hierarchy, animation.channels,
                         rig, apply_uncompressed)
    else:
        process_channels(context, hierarchy, animation.time_coded_channels,
                         rig, apply_timecoded)
        process_channels(context, hierarchy, animation.adaptive_delta_channels,
                         rig, apply_adaptive_delta)
        process_motion_channels(context, hierarchy, animation.motion_channels, rig)

    bpy.context.scene.frame_set(0)