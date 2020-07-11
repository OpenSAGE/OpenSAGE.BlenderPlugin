# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from mathutils import Vector, Quaternion, Matrix
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.utils.primitives import *


def get_or_create_skeleton(hierarchy, coll):
    if hierarchy is None:
        return None

    name = hierarchy.header.name.upper()
    for obj in bpy.data.objects:
        if obj.name.upper() == name and obj.type == 'ARMATURE':
            return obj

    return create_bone_hierarchy(hierarchy, coll)


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


def create_bone_hierarchy(hierarchy, coll):
    root = hierarchy.pivots[0]
    rig, armature = create_rig(hierarchy.name(), root, coll)

    for pivot in hierarchy.pivots:
        if pivot.parent_id < 0:
            continue

        bone = armature.edit_bones.new(pivot.name)
        matrix = make_transform_matrix(pivot.translation, pivot.rotation)

        if pivot.parent_id > 0:
            parent_pivot = hierarchy.pivots[pivot.parent_id]
            bone.parent = armature.edit_bones[parent_pivot.name]
            matrix = bone.parent.matrix @ matrix

        bone.head = Vector((0.0, 0.0, 0.0))
        bone.tail = Vector((0.0, 0.0, 0.01))
        bone.matrix = matrix

    bpy.ops.object.mode_set(mode='POSE')
    basic_sphere = create_sphere()

    for bone in rig.pose.bones:
        bone.custom_shape = basic_sphere

    bpy.ops.object.mode_set(mode='OBJECT')
    return rig
