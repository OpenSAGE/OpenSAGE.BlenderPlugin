# <pep8 compliant>
"""Automatic skeleton binding.

Adds an Armature modifier to every unbound mesh in the scene and weights each
of its vertices to its nearest bone(s): rigidly (100%) if only one bone is
clearly closest, or blended by inverse distance - favouring whichever bone is
closer, not a flat split - if a second one is nearly as close, which is what
sitting near a joint boundary looks like. This was calibrated against several
real exported assets, both hard-surface (armor, weapons - almost always rigid)
and organic (creatures, cloth - blended near roughly a third of their
vertices); see BLEND_RATIO_THRESHOLD for what that calibration did and did not
find. A 'Show Weights' toggle bakes the result into a vertex color layer,
gives each bone a small colored marker sphere and a visible name (a W3D
hierarchy's pivot bones are usually near zero length and otherwise easy to
miss entirely), and switches the 3D viewport to show it all, so a vertex whose
weights do not sum to 100% is obvious at a glance.
"""

import colorsys
import math

import bmesh
import bpy
import numpy as np
from bpy.props import BoolProperty, PointerProperty
from bpy.types import Operator

from .. import utils

# Auto-Bind calls nearest_bone_weights() with this many candidate bones per
# vertex; whether a vertex actually ends up using more than one of them is
# decided by BLEND_RATIO_THRESHOLD, not by this number
AUTO_BIND_MAX_BONES = 2
# a second (or third, ...) bone only contributes if its distance is within this
# multiple of the nearest bone's - otherwise its weight is zeroed out and the
# vertex ends up rigidly bound to just its nearest bone. Fit by comparing
# candidate thresholds against real assets (see the module docstring): no
# threshold reliably predicted any individual real model's exact choice - hand
# weight-painting depends on body topology a pure distance measure cannot see
# - so this is chosen to bias toward staying rigid unless a vertex is clearly
# near a joint, since wrongly blending a hard-surface part is more visibly
# wrong than leaving a genuine joint vertex rigid
BLEND_RATIO_THRESHOLD = 1.2
DISTANCE_EPSILON = 1e-6
# how far a vertex's total weight (restricted to this armature's bones) may drift
# from 1.0 and still count as fine; float weights are never exactly 1.0
WEIGHT_SUM_TOLERANCE = 0.02

WEIGHT_COLOR_ATTRIBUTE = 'bfme_bind_weights'
# a problem (weights not summing to 100%, whatever the bone count) is shown in
# plain white, which never occurs in the hue sweep bone_color() produces
PROBLEM_COLOR = (1.0, 1.0, 1.0)

BONE_MARKER_NAME = 'bfme_bind_bone_marker'
# a small sphere on every bone, sized as a fraction of the armature's own
# overall size, so imported W3D hierarchies - whose pivot bones are usually
# near zero length - get a consistently sized, visible marker regardless of
# how big or small the model itself is
BONE_MARKER_RELATIVE_SIZE = 0.015
BONE_MARKER_MIN_RADIUS = 0.05


##########################################################################
# vertex -> bone assignment (pure numpy, no bpy access, unit testable)
##########################################################################


def closest_point_distances(points, heads, tails):
    """(P, B) distance from each point to each bone segment (head -> tail)."""
    if not len(heads):
        return np.empty((len(points), 0))

    ab = tails - heads  # (B, 3)
    ab_len_sq = np.sum(ab * ab, axis=1)  # (B,)
    # a zero-length bone (head == tail) degenerates to a point distance
    ab_len_sq_safe = np.where(ab_len_sq < 1e-12, 1.0, ab_len_sq)

    ap = points[:, None, :] - heads[None, :, :]  # (P, B, 3)
    t = np.einsum('pbc,bc->pb', ap, ab) / ab_len_sq_safe[None, :]
    t = np.clip(t, 0.0, 1.0)

    closest = heads[None, :, :] + t[:, :, None] * ab[None, :, :]  # (P, B, 3)
    diff = points[:, None, :] - closest
    return np.sqrt(np.sum(diff * diff, axis=2))


def nearest_bone_weights(distances, max_bones=2, blend_ratio_threshold=BLEND_RATIO_THRESHOLD):
    """The nearest bone(s) per point and their normalised weights.

    distances is a (P, B) matrix. Returns (indices, weights), both (P, k) with
    k = min(max_bones, B); every row of weights sums to 1.0. The nearest bone
    (slot 0) always contributes; a further one only does if it is within
    `blend_ratio_threshold` times the nearest bone's own distance - otherwise
    its weight is 0 and the point ends up rigidly bound to just its nearest
    bone. Where more than one bone does contribute, weight is inverse-distance,
    so the closer of the two dominates rather than an even split.
    """
    point_count, bone_count = distances.shape
    k = min(max_bones, bone_count)
    if k == 0:
        return (np.empty((point_count, 0), dtype=np.int64),
                np.empty((point_count, 0), dtype=np.float64))

    if k == bone_count:
        candidates = np.tile(np.arange(bone_count), (point_count, 1))
    else:
        # argpartition only guarantees the k smallest are in the first k slots,
        # not that they are sorted among themselves - sorted below instead
        candidates = np.argpartition(distances, k - 1, axis=1)[:, :k]

    candidate_dist = np.take_along_axis(distances, candidates, axis=1)
    # sort ascending so slot 0 is reliably the single nearest bone, which the
    # ratio cutoff below is relative to
    order = np.argsort(candidate_dist, axis=1)
    indices = np.take_along_axis(candidates, order, axis=1)
    nearest = np.take_along_axis(candidate_dist, order, axis=1)

    raw_weight = 1.0 / (nearest + DISTANCE_EPSILON)
    if k > 1:
        within_range = nearest <= nearest[:, :1] * blend_ratio_threshold
        raw_weight = np.where(within_range, raw_weight, 0.0)

    weights = raw_weight / raw_weight.sum(axis=1, keepdims=True)
    return indices, weights


##########################################################################
# weight visualisation (pure, no bpy access, unit testable)
##########################################################################


def bone_color(index, total):
    """A stable, distinct RGB color for the bone at this position in its armature."""
    hue = (index / total) % 1.0 if total else 0.0
    return colorsys.hsv_to_rgb(hue, 0.85, 0.95)


def vertex_weight_status(contributions, tolerance=WEIGHT_SUM_TOLERANCE):
    """'ok' or 'problem' for one vertex's (bone_index, weight) contributions,
    restricted to a single armature's bones (unrelated vertex groups, e.g. paint
    masks, are not part of `contributions` and do not affect this).

    The only thing that makes a binding a problem is its total weight not
    summing to 100%, however many bones that weight happens to be spread over -
    an unbound vertex (no contributions, sum 0%) is just the extreme case of it.
    """
    if not contributions:
        return 'problem'
    total = sum(weight for _, weight in contributions)
    return 'ok' if abs(total - 1.0) <= tolerance else 'problem'


def vertex_display_color(contributions, bone_colors, tolerance=WEIGHT_SUM_TOLERANCE):
    """The color to show for one vertex: its bone colors blended by weight, or
    PROBLEM_COLOR if the weights do not sum to ~100%.
    """
    if vertex_weight_status(contributions, tolerance) == 'problem':
        return PROBLEM_COLOR

    red = green = blue = 0.0
    for bone_index, weight in contributions:
        color = bone_colors[bone_index]
        red += color[0] * weight
        green += color[1] * weight
        blue += color[2] * weight
    return red, green, blue


##########################################################################
# bpy glue
##########################################################################


def _deform_bone_segments(armature_obj):
    """(names, heads, tails) of every deform bone, in world space.

    Rest pose positions (head_local/tail_local) are used rather than the current
    pose, matching how a bind is normally done: once, before the skeleton moves.
    """
    matrix = np.array(armature_obj.matrix_world, dtype=np.float64)

    names = []
    local_heads = []
    local_tails = []
    for bone in armature_obj.data.bones:
        if not bone.use_deform:
            continue
        names.append(bone.name)
        local_heads.append(tuple(bone.head_local))
        local_tails.append(tuple(bone.tail_local))

    if not names:
        return [], np.empty((0, 3)), np.empty((0, 3))

    heads = np.asarray(local_heads, dtype=np.float64) @ matrix[:3, :3].T + matrix[:3, 3]
    tails = np.asarray(local_tails, dtype=np.float64) @ matrix[:3, :3].T + matrix[:3, 3]
    return names, heads, tails


def _has_armature_modifier(obj, armature_obj=None):
    for modifier in obj.modifiers:
        if modifier.type != 'ARMATURE':
            continue
        if armature_obj is None or modifier.object == armature_obj:
            return True
    return False


def loose_mesh_objects(scene):
    """Mesh objects with no Armature modifier at all: what Auto-Bind acts on."""
    return [obj for obj in scene.objects if obj.type == 'MESH' and not _has_armature_modifier(obj)]


def bound_mesh_objects(scene, armature_obj):
    """Mesh objects whose Armature modifier targets this specific armature."""
    return [obj for obj in scene.objects
            if obj.type == 'MESH' and _has_armature_modifier(obj, armature_obj)]


def bind_object_to_armature(obj, armature_obj, bone_names, heads, tails):
    """Add the Armature modifier and weight every vertex to its nearest bone(s):
    rigidly if only one is clearly closest, blended by inverse distance if a
    second one is nearly as close (see nearest_bone_weights()).

    Any existing vertex groups named after one of this armature's bones are
    replaced, so running this twice does not leave a vertex in a group it is no
    longer actually weighted to.
    """
    mesh = obj.data
    if not len(mesh.vertices):
        return False

    coords = utils.mesh_world_coords(obj)
    distances = closest_point_distances(coords, heads, tails)
    indices, weights = nearest_bone_weights(distances, max_bones=AUTO_BIND_MAX_BONES)

    for name in bone_names:
        group = obj.vertex_groups.get(name)
        if group is not None:
            obj.vertex_groups.remove(group)

    groups = {}
    slot_count = indices.shape[1]
    for vertex_index in range(len(mesh.vertices)):
        for slot in range(slot_count):
            weight = float(weights[vertex_index, slot])
            if weight <= 0.0:
                continue  # a candidate bone that did not make the blend cutoff
            bone_index = int(indices[vertex_index, slot])
            name = bone_names[bone_index]
            group = groups.get(name)
            if group is None:
                group = obj.vertex_groups.new(name=name)
                groups[name] = group
            group.add([vertex_index], weight, 'REPLACE')

    modifier = next((m for m in obj.modifiers if m.type == 'ARMATURE'), None)
    if modifier is None:
        modifier = obj.modifiers.new(name='Armature', type='ARMATURE')
    modifier.object = armature_obj

    return True


class BFME_OT_auto_bind(Operator):
    """Bind every unbound mesh in the scene to the selected armature"""
    bl_idname = 'bfme.auto_bind'
    bl_label = 'Auto-Bind'
    bl_description = 'Add an Armature modifier to every loose mesh and weight its vertices to the nearest bone(s)'

    def execute(self, context):
        scene = context.scene
        armature_obj = scene.bfme_bind_target

        if armature_obj is None or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'Please select an armature first.')
            return {'CANCELLED'}

        bone_names, heads, tails = _deform_bone_segments(armature_obj)
        if not bone_names:
            self.report({'ERROR'}, f"'{armature_obj.name}' has no deforming bones.")
            return {'CANCELLED'}

        loose = loose_mesh_objects(scene)
        if not loose:
            self.report({'WARNING'}, 'No loose mesh objects found (every mesh already has an Armature modifier).')
            return {'CANCELLED'}

        bound = sum(1 for obj in loose if bind_object_to_armature(obj, armature_obj, bone_names, heads, tails))

        if scene.bfme_bind_show_weights:
            refresh_weight_display(scene)

        self.report({'INFO'}, f"Bound {bound} object(s) to '{armature_obj.name}'")
        return {'FINISHED'}


def _apply_weight_colors(obj, bone_index_by_name, bone_colors):
    mesh = obj.data
    vertex_count = len(mesh.vertices)
    if not vertex_count:
        return

    group_to_bone = {group.index: bone_index_by_name[group.name]
                      for group in obj.vertex_groups if group.name in bone_index_by_name}

    colors = np.empty((vertex_count, 4), dtype=np.float32)
    colors[:, 3] = 1.0

    for vertex in mesh.vertices:
        contributions = [(group_to_bone[element.group], element.weight)
                          for element in vertex.groups
                          if element.group in group_to_bone and element.weight > 1e-6]
        colors[vertex.index, :3] = vertex_display_color(contributions, bone_colors)

    color_attr = mesh.color_attributes.get(WEIGHT_COLOR_ATTRIBUTE)
    if color_attr is None:
        color_attr = mesh.color_attributes.new(name=WEIGHT_COLOR_ATTRIBUTE, type='BYTE_COLOR', domain='POINT')
    color_attr.data.foreach_set('color', colors.ravel())

    index = mesh.color_attributes.find(WEIGHT_COLOR_ATTRIBUTE)
    mesh.color_attributes.active_color_index = index
    mesh.color_attributes.render_color_index = index


def _remove_weight_colors(obj):
    mesh = getattr(obj, 'data', None)
    if mesh is None or not hasattr(mesh, 'color_attributes'):
        return
    color_attr = mesh.color_attributes.get(WEIGHT_COLOR_ATTRIBUTE)
    if color_attr is not None:
        mesh.color_attributes.remove(color_attr)


def _set_viewport_display(show):
    """Solid shading with vertex colors, plus the wireframe overlay so the mesh
    structure stays visible - a real wireframe shading type cannot show colors
    at all, it only ever draws edges.
    """
    window_manager = getattr(bpy.context, 'window_manager', None)
    if window_manager is None:
        return

    for window in window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                if show:
                    space.shading.type = 'SOLID'
                    space.shading.color_type = 'VERTEX'
                    space.overlay.show_wireframes = True
                else:
                    space.shading.color_type = 'MATERIAL'
                    space.overlay.show_wireframes = False


def _enter_pose_mode(armature_obj):
    """Custom bone colors are only drawn in Edit or Pose Mode; Object Mode always
    shows the plain default bone shape regardless of Bone.color. Pose Mode is the
    non-destructive one of the two, so that is what gets entered here.
    """
    view_layer = bpy.context.view_layer
    if view_layer is None or armature_obj.mode == 'POSE':
        return
    try:
        previous_active = view_layer.objects.active
        view_layer.objects.active = armature_obj
        armature_obj.select_set(True)
        with bpy.context.temp_override(active_object=armature_obj, object=armature_obj):
            bpy.ops.object.mode_set(mode='POSE')
        view_layer.objects.active = previous_active
    except RuntimeError as error:
        print(f'[BFME_BIND] could not enter Pose Mode on {armature_obj.name!r}: {error}')


def _exit_pose_mode(armature_obj):
    try:
        if armature_obj.mode != 'POSE':
            return
        with bpy.context.temp_override(active_object=armature_obj, object=armature_obj):
            bpy.ops.object.mode_set(mode='OBJECT')
    except (RuntimeError, ReferenceError) as error:
        # ReferenceError: the armature could have been deleted while shown
        print(f'[BFME_BIND] could not leave Pose Mode: {error}')


def _bone_marker_mesh():
    mesh = bpy.data.meshes.get(BONE_MARKER_NAME)
    if mesh is not None:
        return mesh

    mesh = bpy.data.meshes.new(BONE_MARKER_NAME)
    b_mesh = bmesh.new()
    bmesh.ops.create_uvsphere(b_mesh, u_segments=8, v_segments=6, radius=1.0)
    b_mesh.to_mesh(mesh)
    b_mesh.free()
    return mesh


def _bone_marker_object():
    """A single small sphere shared as every bone's custom shape. Deliberately
    not linked into any collection: it only ever exists as a shape source, not
    as a scene object of its own.
    """
    obj = bpy.data.objects.get(BONE_MARKER_NAME)
    if obj is not None:
        return obj
    return bpy.data.objects.new(BONE_MARKER_NAME, _bone_marker_mesh())


def _bone_marker_radius(armature_obj):
    """World-space marker radius: a small, consistent fraction of the
    armature's overall size, so it scales sensibly across differently sized
    models instead of using one fixed absolute size.
    """
    diagonal = math.sqrt(sum(d * d for d in armature_obj.dimensions))
    return max(diagonal * BONE_MARKER_RELATIVE_SIZE, BONE_MARKER_MIN_RADIUS)


def _apply_bone_markers(armature_obj):
    """Give every bone a small colored sphere and show its name. A W3D
    hierarchy's pivot bones are usually near zero length, easy to miss
    entirely without this.
    """
    marker = _bone_marker_object()
    radius = _bone_marker_radius(armature_obj)

    for pose_bone in armature_obj.pose.bones:
        pose_bone.custom_shape = marker
        pose_bone.use_custom_shape_bone_size = False
        pose_bone.custom_shape_scale_xyz = (radius, radius, radius)

    armature_obj.data.show_names = True
    # otherwise hidden behind whatever mesh the bone sits inside of
    armature_obj.show_in_front = True


def _remove_bone_markers(armature_obj):
    if armature_obj is not None:
        try:
            for pose_bone in armature_obj.pose.bones:
                pose_bone.custom_shape = None
            armature_obj.data.show_names = False
            armature_obj.show_in_front = False
        except ReferenceError:
            pass  # the armature was deleted while its weights were shown

    marker = bpy.data.objects.get(BONE_MARKER_NAME)
    if marker is not None and marker.users == 0:
        mesh = marker.data
        bpy.data.objects.remove(marker)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


# the armature Show Weights is currently visualising, if any - tracked so
# turning the display off (or switching targets) can clean up Pose Mode and
# the bone markers on the right one even after scene.bfme_bind_target has
# since changed, without touching an unrelated armature elsewhere in the scene
_visualized_armature = None


def refresh_weight_display(scene):
    """(Re)colors every mesh currently bound to the target armature, marks its
    bones, and turns the viewport display on. Does nothing if there is no
    valid target; the panel disables the checkbox in that case so this should
    not normally be reachable.
    """
    global _visualized_armature

    armature_obj = scene.bfme_bind_target
    if armature_obj is None or armature_obj.type != 'ARMATURE':
        return

    bone_names = [bone.name for bone in armature_obj.data.bones]
    if not bone_names:
        return

    if _visualized_armature is not None and _visualized_armature != armature_obj:
        for obj in bound_mesh_objects(scene, _visualized_armature):
            _remove_weight_colors(obj)
        _remove_bone_markers(_visualized_armature)
        _exit_pose_mode(_visualized_armature)

    _visualized_armature = armature_obj

    bone_colors = [bone_color(index, len(bone_names)) for index in range(len(bone_names))]
    for index, bone in enumerate(armature_obj.data.bones):
        bone.color.palette = 'CUSTOM'
        bone.color.custom.normal = bone_colors[index]

    bone_index_by_name = {name: index for index, name in enumerate(bone_names)}
    for obj in bound_mesh_objects(scene, armature_obj):
        _apply_weight_colors(obj, bone_index_by_name, bone_colors)

    _enter_pose_mode(armature_obj)
    _apply_bone_markers(armature_obj)
    _set_viewport_display(True)


def _update_show_weights(self, _context):
    global _visualized_armature

    scene = self
    if scene.bfme_bind_show_weights:
        refresh_weight_display(scene)
        return

    armature_obj = _visualized_armature
    _visualized_armature = None

    _set_viewport_display(False)
    for obj in scene.objects:
        if obj.type == 'MESH':
            _remove_weight_colors(obj)
    _remove_bone_markers(armature_obj)
    if armature_obj is not None:
        _exit_pose_mode(armature_obj)


def _update_bind_target(self, context):
    if not self.bfme_bind_show_weights:
        return
    if self.bfme_bind_target is None:
        # nothing left to show a visualisation for; this also cleans it up
        self.bfme_bind_show_weights = False
        return
    refresh_weight_display(self)


##########################################################################
# panel
##########################################################################


def draw(layout, scene):
    layout.prop(scene, 'bfme_bind_target')

    has_target = scene.bfme_bind_target is not None

    row = layout.row()
    row.enabled = has_target
    row.operator('bfme.auto_bind', icon='ARMATURE_DATA')

    row = layout.row()
    row.enabled = has_target
    row.prop(scene, 'bfme_bind_show_weights')

    if has_target and scene.bfme_bind_show_weights:
        box = layout.box()
        box.label(text='White = a vertex\'s weights do not sum to 100%', icon='ERROR')


CLASSES = (BFME_OT_auto_bind,)

SCENE_PROPERTIES = ('bfme_bind_target', 'bfme_bind_show_weights')


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    scene = bpy.types.Scene
    scene.bfme_bind_target = PointerProperty(
        type=bpy.types.Object,
        name='Skeleton',
        description='The armature to bind loose meshes to',
        poll=lambda self, obj: obj.type == 'ARMATURE',
        update=_update_bind_target)
    scene.bfme_bind_show_weights = BoolProperty(
        name='Show Weights',
        description='Color vertices and bones by binding, and flag anything not summing to 100% in white',
        default=False,
        update=_update_show_weights)


def unregister():
    global _visualized_armature
    _visualized_armature = None

    marker = bpy.data.objects.get(BONE_MARKER_NAME)
    if marker is not None:
        mesh = marker.data
        bpy.data.objects.remove(marker)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    for name in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
