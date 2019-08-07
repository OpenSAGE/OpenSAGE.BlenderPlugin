import os
import bpy
from mathutils import Vector, Quaternion

#######################################################################################
# helper methods
#######################################################################################

def InsensitiveOpen(path):
    #find the file on unix
    dir = os.path.dirname(path)
    name = os.path.basename(path)

    for filename in os.listdir(dir):
        if filename.lower()==name.lower():
            path = os.path.join(dir,filename)
            return open(path,"rb")

def InsensitivePath(path):
     #find the file on unix
    dir = os.path.dirname(path)
    name = os.path.basename(path)

    for filename in os.listdir(dir):
        if filename.lower()==name.lower():
            path = os.path.join(dir,filename)
    return path

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

#######################################################################################
# loadTexture
#######################################################################################

def load_texture(self, mesh, texName, tex_type, destBlend):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    default_tex = script_directory + "/default_tex.dds"

    found_img = False
    basename = os.path.splitext(texName)[0]

    #test if image file has already been loaded
    for image in bpy.data.images:
        if basename == os.path.splitext(image.name)[0]:
            img = image
            found_img = True

    # Create texture slot in material
    mTex = mesh.materials[0].texture_slots.add()
    mTex.use_map_alpha = True

    if found_img == False:
        tgapath = os.path.dirname(self.filepath) + "/" + basename + ".tga"
        ddspath = os.path.dirname(self.filepath) + "/" + basename + ".dds"
        tgapath = InsensitivePath(tgapath)
        ddspath = InsensitivePath(ddspath)
        img = None

        try:
            img = bpy.data.images.load(tgapath)
        except:
            try:
                img = bpy.data.images.load(ddspath)
            except:
                self.report({'ERROR'}, "Cannot load texture " + basename)
                print("!!! texture file not found " + basename)
                img = bpy.data.images.load(default_tex)

        cTex = bpy.data.textures.new(texName, type = 'IMAGE')
        cTex.image = img

        if destBlend == 0:
            cTex.use_alpha = True
        else:
            cTex.use_alpha = False

        if tex_type == "normal":
            cTex.use_normal_map = True
            cTex.filter_size = 0.1
            cTex.use_filter_size_min = True

        mTex.texture = cTex
    else:
        mTex.texture = bpy.data.textures[texName]

    mTex.texture_coords = 'UV'
    mTex.mapping = 'FLAT'

    if tex_type == "normal":
       mTex.normal_map_space = 'TANGENT'
       mTex.use_map_color_diffuse = False
       mTex.use_map_normal = True
       mTex.normal_factor = 1.0
       mTex.diffuse_color_factor = 0.0
