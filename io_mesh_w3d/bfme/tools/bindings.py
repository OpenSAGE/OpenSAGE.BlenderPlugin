# <pep8 compliant>
"""Automatic skeleton binding.

Adds an Armature modifier to every unbound mesh in the scene and weights each of
its vertices to the nearest one or two bones, always summing to exactly 100%. A
'Show Weights' toggle bakes the result into a vertex color layer and switches the
3D viewport to show it, so a wrong or over-bound vertex is obvious at a glance.
"""

import colorsys

import bpy
import numpy as np
from bpy.props import BoolProperty, PointerProperty
from bpy.types import Operator

from .. import utils

MAX_BONES_PER_VERTEX = 2
DISTANCE_EPSILON = 1e-6
# how far a vertex's total weight (restricted to this armature's bones) may drift
# from 1.0 and still count as fine; float weights are never exactly 1.0
WEIGHT_SUM_TOLERANCE = 0.02

WEIGHT_COLOR_ATTRIBUTE = 'bfme_bind_weights'
# unmistakably not a bone color: saturated magenta does not occur in the hue
# sweep _bone_color() produces
PROBLEM_COLOR = (1.0, 0.0, 1.0)


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


def nearest_bone_weights(distances, max_bones=MAX_BONES_PER_VERTEX):
    """The up to `max_bones` nearest bones per point and their normalised weights.

    distances is a (P, B) matrix. Returns (indices, weights), both (P, k) with
    k = min(max_bones, B); every row of weights sums to 1.0, which together with
    k <= max_bones is what keeps a vertex within 'at most 2 bones, exactly 100%'.
    """
    point_count, bone_count = distances.shape
    k = min(max_bones, bone_count)
    if k == 0:
        return (np.empty((point_count, 0), dtype=np.int64),
                np.empty((point_count, 0), dtype=np.float64))

    if k == bone_count:
        indices = np.tile(np.arange(bone_count), (point_count, 1))
    else:
        # argpartition only guarantees the k smallest are in the first k slots,
        # not that they are sorted among themselves - fine, order does not matter
        indices = np.argpartition(distances, k - 1, axis=1)[:, :k]

    nearest = np.take_along_axis(distances, indices, axis=1)
    raw_weight = 1.0 / (nearest + DISTANCE_EPSILON)
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
    """
    if not contributions or len(contributions) > MAX_BONES_PER_VERTEX:
        return 'problem'
    total = sum(weight for _, weight in contributions)
    return 'ok' if abs(total - 1.0) <= tolerance else 'problem'


def vertex_display_color(contributions, bone_colors, tolerance=WEIGHT_SUM_TOLERANCE):
    """The color to show for one vertex: its bone colors blended by weight, or
    PROBLEM_COLOR if it is not bound to at most 2 bones summing to ~100%.
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
    """Add the Armature modifier and weight every vertex to its nearest bone(s).

    Any existing vertex groups named after one of this armature's bones are
    replaced, so running this twice does not leave a vertex in a group it is no
    longer actually weighted to.
    """
    mesh = obj.data
    if not len(mesh.vertices):
        return False

    coords = utils.mesh_world_coords(obj)
    distances = closest_point_distances(coords, heads, tails)
    indices, weights = nearest_bone_weights(distances)

    for name in bone_names:
        group = obj.vertex_groups.get(name)
        if group is not None:
            obj.vertex_groups.remove(group)

    groups = {}
    slot_count = indices.shape[1]
    for vertex_index in range(len(mesh.vertices)):
        for slot in range(slot_count):
            bone_index = int(indices[vertex_index, slot])
            weight = float(weights[vertex_index, slot])
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


# the armature this module itself put into Pose Mode, if any - tracked so
# turning the display off exits Pose Mode on the right one even if the target
# was since switched or cleared, without touching an unrelated armature some
# other part of the scene happens to have in Pose Mode
_pose_mode_owner = None


def _enter_pose_mode(armature_obj):
    """Custom bone colors are only drawn in Edit or Pose Mode; Object Mode always
    shows the plain default bone shape regardless of Bone.color. Pose Mode is the
    non-destructive one of the two, so that is what gets entered here.
    """
    global _pose_mode_owner

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
        _pose_mode_owner = armature_obj
    except RuntimeError as error:
        print(f'[BFME_BIND] could not enter Pose Mode on {armature_obj.name!r}: {error}')


def _exit_owned_pose_mode():
    global _pose_mode_owner

    armature_obj = _pose_mode_owner
    _pose_mode_owner = None
    if armature_obj is None:
        return

    try:
        if armature_obj.mode != 'POSE':
            return
        with bpy.context.temp_override(active_object=armature_obj, object=armature_obj):
            bpy.ops.object.mode_set(mode='OBJECT')
    except (RuntimeError, ReferenceError) as error:
        # ReferenceError: the armature could have been deleted while shown
        print(f'[BFME_BIND] could not leave Pose Mode: {error}')


def refresh_weight_display(scene):
    """(Re)colors every mesh currently bound to the target armature and turns the
    viewport display on. Does nothing if there is no valid target; the panel
    disables the checkbox in that case so this should not normally be reachable.
    """
    armature_obj = scene.bfme_bind_target
    if armature_obj is None or armature_obj.type != 'ARMATURE':
        return

    bone_names = [bone.name for bone in armature_obj.data.bones]
    if not bone_names:
        return

    bone_colors = [bone_color(index, len(bone_names)) for index in range(len(bone_names))]
    for index, bone in enumerate(armature_obj.data.bones):
        bone.color.palette = 'CUSTOM'
        bone.color.custom.normal = bone_colors[index]

    bone_index_by_name = {name: index for index, name in enumerate(bone_names)}
    for obj in bound_mesh_objects(scene, armature_obj):
        _apply_weight_colors(obj, bone_index_by_name, bone_colors)

    _enter_pose_mode(armature_obj)
    _set_viewport_display(True)


def _update_show_weights(self, _context):
    scene = self
    if scene.bfme_bind_show_weights:
        refresh_weight_display(scene)
        return

    _set_viewport_display(False)
    for obj in scene.objects:
        if obj.type == 'MESH':
            _remove_weight_colors(obj)
    _exit_owned_pose_mode()


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
        box.label(text='Magenta = not exactly 2 bones or not 100%', icon='ERROR')


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
        description='Color vertices and bones by binding, and flag anything not bound to exactly 1-2 bones at 100%',
        default=False,
        update=_update_show_weights)


def unregister():
    global _pose_mode_owner
    _pose_mode_owner = None

    for name in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
