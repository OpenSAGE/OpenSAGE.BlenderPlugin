# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from unittest.mock import patch
from mathutils import Vector
from io_mesh_w3d.common.utils.mesh_import import *
from io_mesh_w3d.common.utils.hierarchy_import import *
from io_mesh_w3d.common.utils.animation_import import *
from io_mesh_w3d.common.utils.animation_export import *
from tests.common.helpers.mesh import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.animation import *
from tests.w3d.helpers.compressed_animation import *
from tests.utils import *


class TestAnimationUtils(TestCase):
    def test_user_is_notified_if_mesh_is_falsely_animated(self):
        create_mesh(self, get_mesh('mesh'), get_collection())

        mesh = bpy.data.objects['mesh']
        mesh.location = Vector((0, 0, 0))
        mesh.keyframe_insert(data_path='location', index=0, frame=0)

        mesh.location = Vector((2, 2, 2))
        mesh.keyframe_insert(data_path='location', index=0, frame=2)

        with (patch.object(self, 'warning')) as warning_func:
            retrieve_animation(self, 'ani_name', get_hierarchy(), None, False)

            warning_func.assert_called_with('Mesh \'mesh\' is animated, animate its parent bone instead!')

    def test_user_is_notified_if_animation_contains_channels_for_nonexisting_bones(self):
        hierarchy = get_hierarchy()
        animation = get_animation()

        animation.channels = [get_animation_channel(type=CHANNEL_VIS, pivot=len(hierarchy.pivots))]

        rig = get_or_create_skeleton(hierarchy, get_collection())

        with (patch.object(self, 'warning')) as warning_func:
            create_animation(self, rig, animation, hierarchy)
            warning_func.assert_called_with(f'animation channel for bone with ID \'{len(hierarchy.pivots)}\' is invalid -> armature has only {len(hierarchy.pivots)} bones!')

        ani = retrieve_animation(self, 'ani_name', hierarchy, rig, False)

        self.assertEqual(0, len(ani.channels))

    def test_user_is_notified_if_animation_contains_channels_for_nonexisting_bones_compressed(self):
        hierarchy = get_hierarchy()
        animation = get_compressed_animation_empty()

        animation.motion_channels = [get_motion_channel(0, 0, 22, pivot=len(hierarchy.pivots))]

        rig = get_or_create_skeleton(hierarchy, get_collection())

        with (patch.object(self, 'warning')) as warning_func:
            create_animation(self, rig, animation, hierarchy)
            warning_func.assert_called_with(f'animation channel for bone with ID \'{len(hierarchy.pivots)}\' is invalid -> armature has only {len(hierarchy.pivots)} bones!')

        ani = retrieve_animation(self, 'ani_name', hierarchy, rig, False)

        self.assertEqual(0, len(ani.channels))

    def test_retrieve_channels_uncompressed_only_one_frame(self):
        bpy.context.scene.frame_end = 2
        bpy.context.scene.frame_end = 10

        hiera = get_hierarchy()
        rig = get_or_create_skeleton(hiera, get_collection())
        bone = rig.pose.bones[0]
        bone.location = Vector((0, 3, 0))
        bone.keyframe_insert(data_path='location', index=0, frame=3)

        ani = retrieve_animation(self, 'ani_name', hiera, rig, False)

        self.assertEqual(1, ani.channels[0].first_frame)
        self.assertEqual(10, ani.channels[0].last_frame)

    def test_roottransform_visibility_channel_roundtrip(self):
        hierarchy = get_hierarchy()
        animation = get_animation()

        animation.channels = [get_animation_channel(type=CHANNEL_VIS, pivot=0)]

        rig = get_or_create_skeleton(hierarchy, get_collection())

        with (patch.object(self, 'warning')) as warning_func:
            create_animation(self, rig, animation, hierarchy)
            warning_func.assert_called_with(f'armature \'{hierarchy.name()}\' might have been hidden due to visibility animation channels!')

        ani = retrieve_animation(self, 'name', hierarchy, rig, timecoded=False)

        self.assertEqual(1, len(ani.channels))
        self.assertTrue(isinstance(ani.channels[0], AnimationBitChannel))

    def test_quaternions_are_normalized_on_export_uncompressed(self):
        bpy.context.scene.frame_end = 0
        bpy.context.scene.frame_end = 10

        hiera = get_hierarchy()
        rig = get_or_create_skeleton(hiera, get_collection())
        bone = rig.pose.bones[0]
        bone.rotation_quaternion = Quaternion((10, 0, 0, 0))
        bone.keyframe_insert(data_path='rotation_quaternion', frame=0)

        bone.rotation_quaternion = Quaternion((2, 0, -10, 0))
        bone.keyframe_insert(data_path='rotation_quaternion', frame=5)

        bone.rotation_quaternion = Quaternion((5, 5, -5, -5))
        bone.keyframe_insert(data_path='rotation_quaternion', frame=10)

        ani = retrieve_animation(self, 'ani_name', hiera, rig, False)

        self.assertEqual(1, len(ani.channels))
        channel = ani.channels[0]
        self.assertEqual(11, len(channel.data))
        for datum in channel.data:
            self.assertAlmostEqual(1.0, datum.magnitude, 1)

    def test_quaternions_are_normalized_on_export_timecoded(self):
        bpy.context.scene.frame_end = 0

        hiera = get_hierarchy()
        rig = get_or_create_skeleton(hiera, get_collection())
        bone = rig.pose.bones[0]
        bone.rotation_quaternion = Quaternion((10, 0, 0, 0))
        bone.keyframe_insert(data_path='rotation_quaternion', frame=0)

        bone.rotation_quaternion = Quaternion((2, 0, -10, 0))
        bone.keyframe_insert(data_path='rotation_quaternion', frame=5)

        bone.rotation_quaternion = Quaternion((5, 5, -5, -5))
        bone.keyframe_insert(data_path='rotation_quaternion', frame=10)

        ani = retrieve_animation(self, 'ani_name', hiera, rig, True)

        self.assertEqual(1, len(ani.time_coded_channels))
        channel = ani.time_coded_channels[0]
        self.assertEqual(3, len(channel.time_codes))
        for tc in channel.time_codes:
            self.assertAlmostEqual(1.0, tc.value.magnitude, 1)
