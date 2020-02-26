# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from mathutils import Vector, Quaternion, Matrix
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.utils.primitives import *


def get_or_create_skeleton(hlod, hierarchy, coll):
    if hierarchy is None:
        return None

    if hierarchy.header.name in bpy.data.objects and hierarchy.header.name in bpy.data.armatures:
        return bpy.data.objects[hierarchy.header.name]

    sub_objects = []
    if hlod is not None:
        sub_objects = hlod.lod_arrays[-1].sub_objects

    return create_bone_hierarchy(hierarchy, sub_objects, coll)


def create_rig(name, root, coll):
    armature = bpy.data.armatures.new(name)
    armature.show_names = False

    rig = bpy.data.objects.new(name, armature)
    rig.rotation_mode = 'QUATERNION'
    rig.delta_location = root.translation
    rig.delta_rotation_quaternion = root.rotation
    rig.track_axis = 'POS_X'
    link_object_to_active_scene(rig, coll)
    bpy.ops.object.mode_set(mode='EDIT')
    return rig, armature


def create_bone_hierarchy(hierarchy, sub_objects, coll):
    root = hierarchy.pivots[0]
    (rig, armature) = create_rig(hierarchy.name(), root, coll)

    for i, pivot in enumerate(hierarchy.pivots):
        pivot.is_bone = True
        for obj in sub_objects:
            if obj.bone_index == i and obj.name == pivot.name:
                pivot.is_bone = False

    for i, pivot in reversed(list(enumerate(hierarchy.pivots))):
        childs = [child for child in hierarchy.pivots if child.parent_id == i]
        for child in childs:
            if child.is_bone:
                pivot.is_bone = True

    for pivot in hierarchy.pivots:
        if not pivot.is_bone or pivot.parent_id < 0:
            continue

        bone = armature.edit_bones.new(pivot.name)
        matrix = make_transform_matrix(pivot.translation, pivot.rotation)

        if pivot.parent_id > 0:
            parent_pivot = hierarchy.pivots[pivot.parent_id]
            bone.parent = armature.edit_bones[parent_pivot.name]
            matrix = bone.parent.matrix @ matrix

        bone.head = Vector((0.0, 0.0, 0.0))
        # has to point in y direction, so rotation is applied correctly
        bone.tail = Vector((0.0, 0.01, 0.0))
        bone.matrix = matrix

    bpy.ops.object.mode_set(mode='POSE')
    basic_sphere = create_sphere()

    for bone in rig.pose.bones:
        bone.custom_shape = basic_sphere

    bpy.ops.object.mode_set(mode='OBJECT')
    return rig
