# <pep8 compliant>
# Tests for automatic skeleton binding: nearest-bone vertex weighting and its
# 'Show Weights' visualisation.

import numpy as np

import bpy
from mathutils import Vector

from io_mesh_w3d.bfme.tools import bindings
from tests.utils import TestCase


##########################################################################
# pure vertex -> bone assignment, no bpy needed
##########################################################################


class TestClosestPointDistances(TestCase):
    def test_distance_to_a_point_bone_is_euclidean(self):
        points = np.array([[0.0, 0.0, 0.0]])
        heads = np.array([[3.0, 4.0, 0.0]])
        tails = np.array([[3.0, 4.0, 0.0]])  # zero-length bone

        distances = bindings.closest_point_distances(points, heads, tails)

        self.assertAlmostEqual(5.0, distances[0, 0])

    def test_a_point_beside_the_segment_uses_the_perpendicular_distance(self):
        points = np.array([[0.5, 1.0, 0.0]])
        heads = np.array([[0.0, 0.0, 0.0]])
        tails = np.array([[1.0, 0.0, 0.0]])

        distances = bindings.closest_point_distances(points, heads, tails)

        self.assertAlmostEqual(1.0, distances[0, 0])

    def test_a_point_beyond_the_tail_uses_the_tail_distance(self):
        points = np.array([[2.0, 0.0, 0.0]])
        heads = np.array([[0.0, 0.0, 0.0]])
        tails = np.array([[1.0, 0.0, 0.0]])

        distances = bindings.closest_point_distances(points, heads, tails)

        self.assertAlmostEqual(1.0, distances[0, 0])

    def test_no_bones_gives_an_empty_column(self):
        points = np.zeros((3, 3))

        distances = bindings.closest_point_distances(points, np.empty((0, 3)), np.empty((0, 3)))

        self.assertEqual((3, 0), distances.shape)


class TestNearestBoneWeights(TestCase):
    def test_weights_of_a_single_bone_sum_to_one(self):
        distances = np.array([[2.0]])

        indices, weights = bindings.nearest_bone_weights(distances)

        self.assertEqual((1, 1), indices.shape)
        self.assertAlmostEqual(1.0, weights[0].sum())

    def test_never_returns_more_than_two_bones(self):
        distances = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])

        indices, weights = bindings.nearest_bone_weights(distances)

        self.assertEqual(2, indices.shape[1])
        self.assertAlmostEqual(1.0, weights[0].sum())

    def test_picks_the_two_closest_bones(self):
        distances = np.array([[5.0, 1.0, 3.0, 2.0]])

        indices, weights = bindings.nearest_bone_weights(distances)

        self.assertEqual({1, 3}, set(indices[0].tolist()))

    def test_the_closer_bone_gets_more_weight(self):
        distances = np.array([[1.0, 4.0]])

        indices, weights = bindings.nearest_bone_weights(distances)

        weight_by_bone = dict(zip(indices[0].tolist(), weights[0].tolist()))
        self.assertGreater(weight_by_bone[0], weight_by_bone[1])

    def test_weights_are_exactly_normalised_for_many_rows(self):
        rng = np.random.default_rng(0)
        distances = rng.uniform(0.01, 10.0, size=(200, 6))

        _, weights = bindings.nearest_bone_weights(distances)

        sums = weights.sum(axis=1)
        np.testing.assert_allclose(sums, np.ones(200), atol=1e-9)

    def test_no_bones_gives_no_assignment(self):
        distances = np.empty((3, 0))

        indices, weights = bindings.nearest_bone_weights(distances)

        self.assertEqual((3, 0), indices.shape)
        self.assertEqual((3, 0), weights.shape)


##########################################################################
# weight status / visualisation colors, no bpy needed
##########################################################################


class TestVertexWeightStatus(TestCase):
    def test_two_bones_summing_to_one_is_ok(self):
        self.assertEqual('ok', bindings.vertex_weight_status([(0, 0.6), (1, 0.4)]))

    def test_one_bone_at_full_weight_is_ok(self):
        self.assertEqual('ok', bindings.vertex_weight_status([(0, 1.0)]))

    def test_no_bones_is_a_problem(self):
        self.assertEqual('problem', bindings.vertex_weight_status([]))

    def test_more_than_two_bones_is_a_problem(self):
        self.assertEqual('problem', bindings.vertex_weight_status([(0, 0.34), (1, 0.33), (2, 0.33)]))

    def test_weights_not_summing_to_one_is_a_problem(self):
        self.assertEqual('problem', bindings.vertex_weight_status([(0, 0.3), (1, 0.3)]))

    def test_a_tiny_floating_point_drift_is_still_ok(self):
        self.assertEqual('ok', bindings.vertex_weight_status([(0, 0.6000001), (1, 0.3999998)]))


class TestBoneColor(TestCase):
    def test_colors_are_distinct_across_the_sweep(self):
        colors = [bindings.bone_color(index, 5) for index in range(5)]

        self.assertEqual(5, len(set(colors)))

    def test_of_a_single_bone_does_not_divide_by_zero(self):
        color = bindings.bone_color(0, 1)

        self.assertEqual(3, len(color))
        for channel in color:
            self.assertGreaterEqual(channel, 0.0)
            self.assertLessEqual(channel, 1.0)


class TestVertexDisplayColor(TestCase):
    def test_a_problem_vertex_gets_the_problem_color(self):
        color = bindings.vertex_display_color([(0, 0.3), (1, 0.3)], [(1, 0, 0), (0, 1, 0)])

        self.assertEqual(bindings.PROBLEM_COLOR, color)

    def test_a_single_full_weight_bone_shows_its_own_color(self):
        color = bindings.vertex_display_color([(0, 1.0)], [(0.2, 0.4, 0.6)])

        self.assertEqual((0.2, 0.4, 0.6), color)

    def test_two_bones_blend_proportionally(self):
        color = bindings.vertex_display_color([(0, 0.75), (1, 0.25)], [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)])

        self.assertAlmostEqual(0.75, color[0])
        self.assertAlmostEqual(0.25, color[1])


##########################################################################
# real bpy scenes: binding, modifiers, vertex groups
##########################################################################


class BindingsTestCase(TestCase):
    def create_armature(self, bones):
        """bones: {name: (head, tail)}."""
        armature_data = bpy.data.armatures.new('rig')
        armature_obj = bpy.data.objects.new('rig', armature_data)
        bpy.context.scene.collection.objects.link(armature_obj)
        bpy.context.view_layer.objects.active = armature_obj

        bpy.ops.object.mode_set(mode='EDIT')
        for name, (head, tail) in bones.items():
            bone = armature_data.edit_bones.new(name)
            bone.head = head
            bone.tail = tail
        bpy.ops.object.mode_set(mode='OBJECT')
        return armature_obj

    def create_mesh(self, name, vertices):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], [])
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


class TestLooseAndBoundObjects(BindingsTestCase):
    def test_a_mesh_without_an_armature_modifier_is_loose(self):
        obj = self.create_mesh('m', [(0, 0, 0)])

        self.assertEqual([obj], bindings.loose_mesh_objects(bpy.context.scene))

    def test_a_mesh_with_an_armature_modifier_is_not_loose(self):
        obj = self.create_mesh('m', [(0, 0, 0)])
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        modifier = obj.modifiers.new(name='Armature', type='ARMATURE')
        modifier.object = armature

        self.assertEqual([], bindings.loose_mesh_objects(bpy.context.scene))
        self.assertEqual([obj], bindings.bound_mesh_objects(bpy.context.scene, armature))

    def test_bound_mesh_objects_is_specific_to_the_given_armature(self):
        obj = self.create_mesh('m', [(0, 0, 0)])
        armature_a = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        armature_b = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        modifier = obj.modifiers.new(name='Armature', type='ARMATURE')
        modifier.object = armature_a

        self.assertEqual([obj], bindings.bound_mesh_objects(bpy.context.scene, armature_a))
        self.assertEqual([], bindings.bound_mesh_objects(bpy.context.scene, armature_b))


class TestBindObjectToArmature(BindingsTestCase):
    def test_adds_an_armature_modifier_pointing_at_the_skeleton(self):
        armature = self.create_armature({'bone1': ((0, 0, 0), (0, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)

        bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        modifiers = [m for m in obj.modifiers if m.type == 'ARMATURE']
        self.assertEqual(1, len(modifiers))
        self.assertEqual(armature, modifiers[0].object)

    def test_a_vertex_next_to_one_bone_is_still_weighted_to_two_when_more_exist(self):
        armature = self.create_armature({
            'near': ((0, 0, 0), (0, 0, 1)),
            'far': ((10, 0, 0), (10, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)

        bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        weights = self._vertex_weights(obj, 0)
        self.assertEqual({'near', 'far'}, set(weights))
        self.assertAlmostEqual(1.0, sum(weights.values()), places=5)
        self.assertGreater(weights['near'], weights['far'])

    def test_never_weights_a_vertex_to_more_than_two_bones(self):
        armature = self.create_armature({
            f'bone{i}': ((i, 0, 0), (i, 0, 1)) for i in range(6)})
        obj = self.create_mesh('m', [(2.5, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)

        bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        weights = self._vertex_weights(obj, 0)
        self.assertLessEqual(len(weights), 2)
        self.assertAlmostEqual(1.0, sum(weights.values()), places=5)

    def test_a_single_bone_armature_gets_full_weight(self):
        armature = self.create_armature({'only': ((0, 0, 0), (0, 0, 1))})
        obj = self.create_mesh('m', [(3, 3, 3)])
        names, heads, tails = bindings._deform_bone_segments(armature)

        bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        weights = self._vertex_weights(obj, 0)
        self.assertEqual({'only': 1.0}, {name: round(weight, 5) for name, weight in weights.items()})

    def test_non_deforming_bones_are_not_considered(self):
        armature = self.create_armature({
            'deform': ((0, 0, 0), (0, 0, 1)),
            'helper': ((0, 0, 5), (0, 0, 6))})
        armature.data.bones['helper'].use_deform = False
        obj = self.create_mesh('m', [(0, 0, 5.5)])  # right next to the helper bone
        names, heads, tails = bindings._deform_bone_segments(armature)

        self.assertEqual(['deform'], names)
        bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        weights = self._vertex_weights(obj, 0)
        self.assertEqual(['deform'], list(weights))

    def test_re_binding_replaces_stale_weights(self):
        """Running Auto-Bind twice must not leave a vertex weighted to a bone it
        is no longer actually closest to.
        """
        armature = self.create_armature({
            'a': ((0, 0, 0), (0, 0, 1)),
            'b': ((5, 0, 0), (5, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)
        bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        # move the vertex to sit exactly on bone 'b' and re-bind
        obj.data.vertices[0].co = Vector((5, 0, 0.5))
        bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        weights = self._vertex_weights(obj, 0)
        self.assertGreater(weights['b'], weights['a'])

    def test_an_object_with_no_vertices_is_left_alone(self):
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        mesh = bpy.data.meshes.new('empty')
        obj = bpy.data.objects.new('empty', mesh)
        bpy.context.scene.collection.objects.link(obj)
        names, heads, tails = bindings._deform_bone_segments(armature)

        result = bindings.bind_object_to_armature(obj, armature, names, heads, tails)

        self.assertFalse(result)
        self.assertEqual(0, len(obj.modifiers))

    @staticmethod
    def _vertex_weights(obj, vertex_index):
        vertex = obj.data.vertices[vertex_index]
        by_group_index = {group.index: group.name for group in obj.vertex_groups}
        return {by_group_index[element.group]: element.weight for element in vertex.groups}


class TestAutoBindOperator(BindingsTestCase):
    def test_binds_every_loose_mesh_to_the_selected_armature(self):
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        first = self.create_mesh('first', [(0, 0, 0.2)])
        second = self.create_mesh('second', [(0, 0, 0.8)])
        bpy.context.scene.bfme_bind_target = armature

        result = bpy.ops.bfme.auto_bind()

        self.assertEqual({'FINISHED'}, result)
        for obj in (first, second):
            self.assertTrue(any(m.type == 'ARMATURE' and m.object == armature for m in obj.modifiers))

    def test_does_not_rebind_an_already_bound_mesh(self):
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        already_bound = self.create_mesh('bound', [(0, 0, 0.5)])
        modifier = already_bound.modifiers.new(name='Armature', type='ARMATURE')
        modifier.object = armature
        bpy.context.scene.bfme_bind_target = armature

        result = bpy.ops.bfme.auto_bind()

        self.assertEqual({'CANCELLED'}, result)  # nothing loose to bind

    def test_fails_without_a_target_armature(self):
        self.create_mesh('m', [(0, 0, 0)])
        bpy.context.scene.bfme_bind_target = None

        # an {'ERROR'} report raises through bpy.ops rather than just returning
        # {'CANCELLED'}, unlike the {'WARNING'} case exercised above
        with self.assertRaises(RuntimeError):
            bpy.ops.bfme.auto_bind()

    def test_fails_when_the_armature_has_no_deforming_bones(self):
        armature = self.create_armature({'helper': ((0, 0, 0), (0, 0, 1))})
        armature.data.bones['helper'].use_deform = False
        self.create_mesh('m', [(0, 0, 0)])
        bpy.context.scene.bfme_bind_target = armature

        with self.assertRaises(RuntimeError):
            bpy.ops.bfme.auto_bind()


class TestWeightColorBaking(BindingsTestCase):
    def test_a_correctly_bound_vertex_is_not_the_problem_color(self):
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)
        bindings.bind_object_to_armature(obj, armature, names, heads, tails)
        bpy.context.scene.bfme_bind_target = armature

        bindings.refresh_weight_display(bpy.context.scene)

        color = self._first_vertex_color(obj)
        self.assertNotEqual(bindings.PROBLEM_COLOR, tuple(round(c, 2) for c in color[:3]))

    def test_an_unbound_vertex_gets_the_problem_color(self):
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        modifier = obj.modifiers.new(name='Armature', type='ARMATURE')
        modifier.object = armature  # bound, but no vertex groups assigned at all
        bpy.context.scene.bfme_bind_target = armature

        bindings.refresh_weight_display(bpy.context.scene)

        color = self._first_vertex_color(obj)
        self.assertEqual(bindings.PROBLEM_COLOR, tuple(round(c, 2) for c in color[:3]))

    def test_an_over_bound_vertex_gets_the_problem_color(self):
        armature = self.create_armature({
            'a': ((0, 0, 0), (0, 0, 1)),
            'b': ((1, 0, 0), (1, 0, 1)),
            'c': ((2, 0, 0), (2, 0, 1))})
        obj = self.create_mesh('m', [(1, 0, 0.5)])
        modifier = obj.modifiers.new(name='Armature', type='ARMATURE')
        modifier.object = armature
        for name, weight in (('a', 0.34), ('b', 0.33), ('c', 0.33)):
            group = obj.vertex_groups.new(name=name)
            group.add([0], weight, 'REPLACE')
        bpy.context.scene.bfme_bind_target = armature

        bindings.refresh_weight_display(bpy.context.scene)

        color = self._first_vertex_color(obj)
        self.assertEqual(bindings.PROBLEM_COLOR, tuple(round(c, 2) for c in color[:3]))

    def test_bones_get_a_custom_color_assigned(self):
        armature = self.create_armature({
            'a': ((0, 0, 0), (0, 0, 1)),
            'b': ((1, 0, 0), (1, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)
        bindings.bind_object_to_armature(obj, armature, names, heads, tails)
        bpy.context.scene.bfme_bind_target = armature

        bindings.refresh_weight_display(bpy.context.scene)

        for bone in armature.data.bones:
            self.assertTrue(bone.color.is_custom)

    @staticmethod
    def _first_vertex_color(obj):
        color_attr = obj.data.color_attributes[bindings.WEIGHT_COLOR_ATTRIBUTE]
        return tuple(color_attr.data[0].color)


class TestShowWeightsToggle(BindingsTestCase):
    def test_toggling_off_removes_the_color_attribute(self):
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)
        bindings.bind_object_to_armature(obj, armature, names, heads, tails)
        scene = bpy.context.scene
        scene.bfme_bind_target = armature

        scene.bfme_bind_show_weights = True
        self.assertIn(bindings.WEIGHT_COLOR_ATTRIBUTE, obj.data.color_attributes)

        scene.bfme_bind_show_weights = False
        self.assertNotIn(bindings.WEIGHT_COLOR_ATTRIBUTE, obj.data.color_attributes)

    def test_entering_and_leaving_pose_mode_is_tracked_by_this_armature_not_the_scene_pointer(self):
        """Bone colors only render in Pose Mode, so turning the toggle on puts the
        target armature there; clearing the target afterwards must still be able
        to take it back out, even though scene.bfme_bind_target no longer points
        at it by the time the cleanup runs.
        """
        armature = self.create_armature({'bone': ((0, 0, 0), (0, 0, 1))})
        obj = self.create_mesh('m', [(0, 0, 0.5)])
        names, heads, tails = bindings._deform_bone_segments(armature)
        bindings.bind_object_to_armature(obj, armature, names, heads, tails)
        scene = bpy.context.scene
        scene.bfme_bind_target = armature

        scene.bfme_bind_show_weights = True
        self.assertEqual('POSE', armature.mode)

        scene.bfme_bind_target = None

        self.assertFalse(scene.bfme_bind_show_weights)
        self.assertEqual('OBJECT', armature.mode)
