# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from mathutils import Quaternion
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.structs.animation import *
from io_mesh_w3d.w3d.structs.compressed_animation import *


def is_rotation(fcu):
    return 'rotation_quaternion' in fcu.data_path


def is_visibility(fcu):
    return 'visibility' in fcu.data_path or 'hide' in fcu.data_path


def retrieve_channels(obj, hierarchy, timecoded, name=None):
    if obj.animation_data is None or obj.animation_data.action is None:
        return []

    channel = None
    channels = []

    for fcu in obj.animation_data.action.fcurves:
        if name is None:
            values = fcu.data_path.split('"')
            if len(values) == 1:
                pivot_name = 'ROOTTRANSFORM'
            else:
                pivot_name = values[1]
        else:
            pivot_name = name

        pivot_index = 0
        for i, pivot in enumerate(hierarchy.pivots):
            if pivot.name == pivot_name:
                pivot_index = i

        channel_type = fcu.array_index
        vec_len = 1

        if is_rotation(fcu):
            channel_type = 6
            vec_len = 4

        if not (channel_type == 6 and fcu.array_index > 0):
            if timecoded:
                channel = TimeCodedAnimationChannel(
                    vector_len=vec_len,
                    type=channel_type,
                    pivot=pivot_index)

                num_keyframes = len(fcu.keyframe_points)
                channel.time_codes = [None] * num_keyframes
                channel.num_time_codes = num_keyframes
            else:
                if is_visibility(fcu):
                    channel = AnimationBitChannel()
                else:
                    channel = AnimationChannel(
                        vector_len=vec_len,
                        type=channel_type)

                channel.data = []
                channel.pivot = pivot_index
                frame_range = fcu.range()
                num_frames = frame_range[1] + 1 - frame_range[0]

                if num_frames == 1:
                    channel.first_frame = bpy.context.scene.frame_start
                    channel.last_frame = bpy.context.scene.frame_end
                else:
                    channel.first_frame = int(frame_range[0])
                    channel.last_frame = int(frame_range[1])
                num_frames = channel.last_frame + 1 - channel.first_frame
                channel.data = [None] * num_frames

        if timecoded:
            for i, keyframe in enumerate(fcu.keyframe_points):
                frame = int(keyframe.co.x)
                val = keyframe.co.y

                if channel_type < 6:
                    channel.time_codes[i] = TimeCodedDatum(
                        time_code=frame,
                        value=val)
                else:
                    if channel.time_codes[i] is None:
                        channel.time_codes[i] = TimeCodedDatum(
                            time_code=frame,
                            value=Quaternion())
                    channel.time_codes[i].value[fcu.array_index] = val
        else:
            for frame in range(channel.first_frame, channel.last_frame + 1):
                val = fcu.evaluate(frame)
                i = frame - channel.first_frame

                if is_visibility(fcu) or channel_type < 6:
                    channel.data[i] = val
                else:
                    if channel.data[i] is None:
                        channel.data[i] = Quaternion((1.0, 0.0, 0.0, 0.0))
                    channel.data[i][fcu.array_index] = val

        if channel_type < 6 or fcu.array_index == 3 or is_visibility(fcu):
            channels.append(channel)
    return channels


def retrieve_animation(context, animation_name, hierarchy, rig, timecoded):
    channels = []

    for mesh in get_objects('MESH'):
        if retrieve_channels(mesh, hierarchy, timecoded, mesh.name):
            context.warning('Mesh \'' + mesh.name + '\' is animated, animate its parent bone instead!')

    if rig is not None:
        channels.extend(retrieve_channels(rig, hierarchy, timecoded))
        channels.extend(retrieve_channels(rig.data, hierarchy, timecoded))

    if timecoded:
        ani_struct = CompressedAnimation(
            header=CompressedAnimationHeader(flavor=TIME_CODED_FLAVOR),
            time_coded_channels=channels)
    else:
        ani_struct = Animation(header=AnimationHeader(), channels=channels)

    ani_struct.header.name = animation_name
    ani_struct.header.hierarchy_name = hierarchy.name()

    start_frame = bpy.context.scene.frame_start
    end_frame = bpy.context.scene.frame_end

    ani_struct.header.num_frames = end_frame + 1 - start_frame
    ani_struct.header.frame_rate = bpy.context.scene.render.fps
    return ani_struct
