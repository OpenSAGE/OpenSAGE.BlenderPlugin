import os
import bpy
from mathutils import Vector, Quaternion

#######################################################################################
# helper methods
#######################################################################################

def skip_unknown_chunk(self, file, chunkType, chunkSize):
    message = "WARNING: unknown chunktype in File: %s" % hex(chunkType)
    #self.report({'ERROR'}, message)
    print(message)
    file.seek(chunkSize, 1)
    
def link_object_to_active_scene(obj):
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
#######################################################################################
# create Armature
#######################################################################################

def create_armature(self, hierarchy, amtName, subObjects):
    amt = bpy.data.armatures.new(hierarchy.header.name)
    amt.show_names = True
    
    rig = bpy.data.objects.new(amtName, amt)
    rig.location = hierarchy.header.centerPos
    rig.rotation_mode = 'QUATERNION'
    #rig.show_x_ray = True
    rig.track_axis = "POS_X"
    
    link_object_to_active_scene(rig)
    bpy.ops.object.mode_set(mode = 'EDIT')

    non_bone_pivots = []

    for obj in subObjects: 
        non_bone_pivots.append(hierarchy.pivots[obj.boneIndex])

    #create the bones from the pivots
    for pivot in hierarchy.pivots:
        if non_bone_pivots.count(pivot) > 0:
                continue #do not create a bone

        bone = amt.edit_bones.new(pivot.name)

        if pivot.parentID > 0:
            parent_pivot =  hierarchy.pivots[pivot.parentID]
            bone.parent = amt.edit_bones[parent_pivot.name]
            
        bone.head = Vector((0.0, 0.0, 0.0))
        #has to point in y direction that the rotation is applied correctly
        bone.tail = Vector((0.0, 1.0, 0.0))

    #pose the bones
    bpy.ops.object.mode_set(mode = 'POSE')

    for pivot in hierarchy.pivots:
        if non_bone_pivots.count(pivot) > 0:
            continue #do not create a bone

        bone = rig.pose.bones[pivot.name]
        bone.location = pivot.position
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_euler = pivot.eulerAngles
        bone.rotation_quaternion = pivot.rotation

    bpy.ops.object.mode_set(mode = 'OBJECT')

    return rig