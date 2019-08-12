# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import os
import bpy
import bmesh
import math

from mathutils import Vector, Quaternion

from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.image_utils import load_image

from bpy.props import FloatVectorProperty, StringProperty, PointerProperty

#######################################################################################
# helper methods
#######################################################################################


def insensitive_open(path):
    print("insensitive open: " + path)
    # find the file on unix
    dir = os.path.dirname(path)
    name = os.path.basename(path)

    for filename in os.listdir(dir):
        if filename.lower() == name.lower():
            path = os.path.join(dir, filename)
            return open(path, "rb")


def insensitive_path(path):
     # find the file on unix
    dir = os.path.dirname(path)
    name = os.path.basename(path)

    for filename in os.listdir(dir):
        if filename.lower() == name.lower():
            path = os.path.join(dir, filename)
    return path


def skip_unknown_chunk(self, file, chunkType, chunkSize):
    message = "WARNING: unknown chunktype in file: %s" % hex(chunkType)
    self.report({'ERROR'}, message)
    print(message)
    file.seek(chunkSize, 1)


def link_object_to_active_scene(obj):
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

#######################################################################################
# create armature
#######################################################################################


def create_armature(self, hierarchy, amtName, subObjects):
    amt = bpy.data.armatures.new(hierarchy.header.name)
    amt.show_names = True

    rig = bpy.data.objects.new(amtName, amt)
    rig.location = hierarchy.header.center
    rig.rotation_mode = 'QUATERNION'
    #rig.show_x_ray = True
    rig.track_axis = "POS_X"

    link_object_to_active_scene(rig)
    bpy.ops.object.mode_set(mode='EDIT')

    non_bone_pivots = []

    basic_sphere = create_sphere()

    for obj in subObjects:
        non_bone_pivots.append(hierarchy.pivots[obj.boneIndex])

    # create the bones from the pivots
    for pivot in hierarchy.pivots:
        if non_bone_pivots.count(pivot) > 0:
            continue  # do not create a bone

        bone = amt.edit_bones.new(pivot.name)

        if pivot.parentID > 0:
            parent_pivot = hierarchy.pivots[pivot.parentID]
            bone.parent = amt.edit_bones[parent_pivot.name]

        bone.head = Vector((0.0, 0.0, 0.0))
        # has to point in y direction that the rotation is applied correctly
        bone.tail = Vector((0.0, 0.01, 0.0))

    # Pose the bones
    bpy.ops.object.mode_set(mode='POSE')

    for pivot in hierarchy.pivots:
        if non_bone_pivots.count(pivot) > 0:
            continue  # do not create a bone

        bone = rig.pose.bones[pivot.name]
        bone.location = pivot.position
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_euler = pivot.eulerAngles
        bone.rotation_quaternion = pivot.rotation

        bone.custom_shape = basic_sphere

    bpy.ops.object.mode_set(mode='OBJECT')

    return rig


#######################################################################################
# create material
#######################################################################################

def create_vert_material(mesh, vertMat):
    mat = bpy.data.materials.new(mesh.header.meshName + "." + vertMat.vmName)
    mat.use_nodes = True
    principled = PrincipledBSDFWrapper(mat, is_readonly=False)
    principled.base_color = (vertMat.vmInfo.diffuse.r,
                             vertMat.vmInfo.diffuse.g,
                             vertMat.vmInfo.diffuse.b)

    # mat.specular_color = (vertMat.vmInfo.specular.r,
    #                       vertMat.vmInfo.specular.g, vertMat.vmInfo.specular.b)
    # mat.diffuse_color = (vertMat.vmInfo.diffuse.r,
    #                      vertMat.vmInfo.diffuse.g, vertMat.vmInfo.diffuse.b,
    #                      vertMat.vmInfo.translucency)
    return mat


def rgba_to_vector(prop):
    return (prop.value.r, prop.value.g, prop.value.b, prop.value.a)


def create_shader_materials(self, m, mesh):
    for material in m.shaderMaterials:
        print("material")
        mat = bpy.data.materials.new(m.header.meshName + ".ShaderMaterial")
        mat.use_nodes = True
        principled = PrincipledBSDFWrapper(mat, is_readonly=False)
        for prop in material.properties:
            print(prop.name)
            print(prop.value)

            if (prop.name == "DiffuseTexture"):
                principled.base_color_texture.image = load_texture(
                    self, prop.value, 0)
            elif (prop.name == "NormalMap"):
                principled.normalmap_texture.image = load_texture(
                    self, prop.value, 0)
            elif (prop.name == "BumpScale"):
                principled.normalmap_strength = prop.value
            # Color type
            elif prop.type == 5:
                mat[prop.name] = rgba_to_vector(prop)
            else:
                mat[prop.name] = prop.value
        mesh.materials.append(mat)

#######################################################################################
# create uvlayer
#######################################################################################


def create_uvlayer(mesh, tris, txCoords, txStages):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    if len(txCoords) > 0:
        uv_layer = mesh.uv_layers.new(name="texcoords", do_init=False)
        index = 0

        for f in bm.faces:
            tri = tris[index]
            for l in f.loops:
                idx = tri[l.index % 3]
                uv_layer.data[l.index].uv = txCoords[idx]
            index += 1

    for stage in txStages:
        i = 0
        if len(stage.txCoords) > 0:
            uv_layer = mesh.uv_layers.new(
                name="texcoords" + str(i), do_init=False)
            index = 0

            for f in bm.faces:
                tri = tris[index]
                for l in f.loops:
                    idx = tri[l.index % 3]
                    uv_layer.data[l.index].uv = stage.txCoords[idx]
                index += 1
            i += 1


#######################################################################################
# load texture
#######################################################################################

def load_texture(self, texName, destBlend):
    found_img = False
    basename = os.path.splitext(texName)[0]

    # Test if the image file already exists
    for image in bpy.data.images:
        if basename.lower() == os.path.splitext(image.name)[0].lower():
            img = image
            found_img = True

    # Try to load the image file
    if found_img == False:
        tgapath = os.path.dirname(self.filepath) + "/" + basename + ".tga"
        ddspath = os.path.dirname(self.filepath) + "/" + basename + ".dds"
        tgapath = insensitive_path(tgapath)
        ddspath = insensitive_path(ddspath)

        img = load_image(tgapath)

        if img == None:
            img = load_image(ddspath)

        if img == None:
            print("missing texture:" + ddspath)

    return img


def load_texture_to_mat(self, texName, destBlend, mat):
    img = load_texture(self, texName, destBlend)
    principled = PrincipledBSDFWrapper(mat, is_readonly=False)
    principled.base_color_texture.image = img


#######################################################################################
# adaptive delta
#######################################################################################

def calculate_table():
    result = []

    for i in range(16):
        result.append(pow(10, i - 8.0))
    
    for i in range(240):
        num = i / 240.0
        result.append(1.0 - math.sin(90.0 * num * math.pi / 180.0))

    return result

delta_table = calculate_table()

def to_signed(byte):
    if byte > 127:
        return (256-byte) * (-1)
    else:
        return byte

def get_deltas(block, numBits):
    deltas = []
    for _ in range(16):
        deltas.append(0x00)

    for i in range(len(block.deltaBytes)):
        index = i * 2
        val = block.deltaBytes[i]
        if numBits == 4:
            deltas[index] = val
            if (deltas[index] & 8) != 0:
                deltas[index] |= 0xF0
            else:
                deltas[index] &= 0x0F
            deltas[index + 1] = val >> 4
        elif numBits == 8:
            if (val & 0x80) != 0:
                val &= 0x7F
            else:
                val |= 0x80
            deltas[i] = to_signed(val)

    return deltas


    #gets AdaptiveDeltaData
def decode(data, channel, scale):
    scaleFactor = 1.0

    if data.bitCount == 8:
        scaleFactor = 1 / 16.0

    result = [None] * channel.numTimeCodes
    result[0] = data.initialValue

    for i in range(1, channel.numTimeCodes):
        if channel.type == 6:
            result[i] = Quaternion()
        else:
            result[i] = 0.0
    

    for i in range(len(data.deltaBlocks)):
        deltaBlock = data.deltaBlocks[i]
        blockIndex = deltaBlock.blockIndex
        blockScale = delta_table[blockIndex]
        deltaScale = blockScale * scale * scaleFactor

        vectorIndex = deltaBlock.vecIndex
        deltas = get_deltas(deltaBlock, data.bitCount)

        for j in range(len(deltas)):
            idx = int(math.floor((i / channel.vectorLen) * 16) + j + 1)
            if idx >= channel.numTimeCodes:
                break

            if channel.type == 6:
                value = result[idx - 1][vectorIndex] + deltaScale * deltas[j]
                result[idx][vectorIndex] = value
            else:
                value = result[idx - 1] + deltaScale * deltas[j]
                result[idx] = result[idx] = value

    return result


#######################################################################################
# createAnimation
#######################################################################################


def is_translation(channel):
    return channel.type == 0 or channel.type == 1 or channel.type == 2


def is_rotation(channel):
    return channel.type == 6

def get_bone(rig, name):
    # sometimes objects are animated, not just bones
    try:
        return rig.pose.bones[name]
    except:
        return bpy.data.objects[name]


def setup_animation(animation):
    rig = bpy.data.objects[animation.header.hierarchyName]
    bpy.data.scenes["Scene"].render.fps = animation.header.frameRate
    bpy.data.scenes["Scene"].frame_start = 0
    bpy.data.scenes["Scene"].frame_end = animation.header.numFrames - 1

    return rig


def init_translation_data(animation, hierarchy):
    translation_data = []
    for pivot in range(0, len(hierarchy.pivots)):
        pivot = []
        for _ in range(0, animation.header.numFrames):
            pivot.append(None)

        translation_data.append(pivot)
    
    return translation_data


def set_trans_data(trans_data, frame, channel, value):
    if (trans_data[frame] == None): 
        trans_data[frame] = Vector((0.0, 0.0, 0.0))
    trans_data[frame][channel.type] = value


# test for setting only one channel at a time (x, y, z)
#def set_translation(bone, rest_location, rest_rotation, index, frame, value):
#    bpy.context.scene.frame_set(frame)
#    vec = Vector((0.0, 0.0, 0.0))
#    vec[index] = value
#    bone.location = rest_location + (rest_rotation @ vec)
#    bone.keyframe_insert(data_path='location', index=index, frame=frame)


def set_rotation(bone, rest_rotation, frame, value):
    bone.rotation_mode = 'QUATERNION'
    bone.rotation_quaternion = rest_rotation @ value
    bone.keyframe_insert(
                data_path='rotation_quaternion', frame=frame)


def apply_timecoded(bone, channel, trans_data, rest_location, rest_rotation):
    for key in channel.timeCodes:
        if is_translation(channel):
            set_trans_data(trans_data[channel.pivot], key.timeCode, channel, key.value)
        elif is_rotation(channel):
            set_rotation(bone, rest_rotation, key.timeCode, key.value)


def apply_motionChannel_timeCoded(bone, channel, trans_data, rest_location, rest_rotation):
    for d in channel.data:
        if is_translation(channel):
            set_trans_data(trans_data[channel.pivot], d.keyFrame, channel, d.value)
        elif is_rotation(channel):
            set_rotation(bone, rest_rotation, d.keyFrame, d.value)


def apply_motionChannel_adaptiveDelta(bone, channel, trans_data, rest_location, rest_rotation):
    for i in range(channel.numTimeCodes):
        print (channel.type)
        if is_translation(channel):
            print(channel.data.data[i])
            set_trans_data(trans_data[channel.pivot], i, channel, channel.data.data[i])
        elif is_rotation(channel):
            print(channel.data.data[i])
            set_rotation(bone, rest_rotation, i, channel.data.data[i])


def apply_uncompressed(bone, channel, trans_data, rest_location, rest_rotation):
    for frame in range(channel.firstFrame, channel.lastFrame):
        if is_translation(channel):
            set_trans_data(trans_data[channel.pivot], frame, channel, channel.data[frame - channel.firstFrame])
        elif is_rotation(channel):
            data = channel.data[frame - channel.firstFrame]
            set_rotation(bone, rest_rotation, frame, data)


def process_channels(hierarchy, channels, rig, translation_data, apply_func):
    for channel in channels:
        if (channel.pivot == 0):
            continue  # skip roottransform

        pivot = hierarchy.pivots[channel.pivot]
        rest_rotation = hierarchy.pivots[channel.pivot].rotation
        rest_location = hierarchy.pivots[channel.pivot].position

        obj = get_bone(rig, pivot.name)

        apply_func(obj, channel, translation_data, rest_location, rest_rotation)


def process_motion_channels(hierarchy, channels, rig, translation_data):
    for channel in channels:
        if (channel.pivot == 0):
            continue  # skip roottransform

        pivot = hierarchy.pivots[channel.pivot]
        rest_rotation = hierarchy.pivots[channel.pivot].rotation
        rest_location = hierarchy.pivots[channel.pivot].position

        obj = get_bone(rig, pivot.name)

        if channel.deltaType == 0:
            apply_motionChannel_timeCoded(obj, channel, translation_data, rest_location, rest_rotation)
        else:
            apply_motionChannel_adaptiveDelta(obj, channel, translation_data, rest_location, rest_rotation)


def apply_final_transform(hierarchy, rig, trans_data, numFrames):
    for pivot in range(1, len(hierarchy.pivots)):
        rest_location = hierarchy.pivots[pivot].position
        rest_rotation = hierarchy.pivots[pivot].rotation

        obj = get_bone(rig, hierarchy.pivots[pivot].name)

        # TODO: check if blender 2.8 supports setting only x/y/z value insted of whole vector
        # this might fix the buggy bfme1 animations
        # -> is supported, but need to apply the rotation -> does not seem to work
        for frame in range(0, numFrames - 1):
            if not trans_data[pivot][frame] == None:
                bpy.context.scene.frame_set(frame)
                pos = trans_data[pivot][frame]
                obj.location = rest_location + (rest_rotation @ pos)
                obj.keyframe_insert(data_path='location', frame=frame)


def create_animation(self, animation, hierarchy, compressed):
    if animation == None:
        return

    rig = setup_animation(animation)
    translation_data = init_translation_data(animation, hierarchy)

    if not compressed:
        process_channels(hierarchy, animation.channels, rig, translation_data, apply_uncompressed)
    else:
        process_channels(hierarchy, animation.timeCodedChannels, rig, translation_data, apply_timecoded)
        process_motion_channels(hierarchy, animation.motionChannels, rig, translation_data)
        print ("motion channels/adaptive delta not supported yet")

    apply_final_transform(hierarchy, rig, translation_data,
                          animation.header.numFrames)


#######################################################################################
# create basic meshes
#######################################################################################

def create_sphere():
    mesh = bpy.data.meshes.new('Basic_Sphere')
    basic_sphere = bpy.data.objects.new("Basic_Sphere", mesh)

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, diameter=35)
    bm.to_mesh(mesh)
    bm.free()

    return basic_sphere


def create_box(box):
    # to keep name always equal (sometimes it is "BOUNDING BOX")
    name = "BOUNDINGBOX"
    x = box.extend[0]/2.0
    y = box.extend[1]/2.0
    z = box.extend[2]

    verts = [(x, y, z), (-x, y, z), (-x, -y, z), (x, -y, z),
             (x, y, 0), (-x, y, 0), (-x, -y, 0), (x, -y, 0)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]

    cube = bpy.data.meshes.new(name)
    b = bpy.data.objects.new(name, cube)
    mat = bpy.data.materials.new("BOUNDINGBOX.Material")

    mat.diffuse_color = (box.color.r, box.color.g, box.color.b, 1.0)
    cube.materials.append(mat)
    b.location = box.center
    link_object_to_active_scene(b)
    cube.from_pydata(verts, [], faces)
    cube.update(calc_edges=True)
