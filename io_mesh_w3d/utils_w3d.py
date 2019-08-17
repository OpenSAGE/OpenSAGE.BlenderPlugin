# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import os
import bpy
import bmesh
import math
import mathutils

from mathutils import Vector, Quaternion

from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.image_utils import load_image

from bpy.props import FloatVectorProperty, StringProperty, PointerProperty

from io_mesh_w3d.w3d_io_binary import *

#######################################################################################
# helper methods
#######################################################################################


def read_array(file, chunkEnd, readFunc):
    result = []
    while file.tell() < chunkEnd:
        result.append(readFunc(file))
    return result


def read_fixed_array(file, count, readFunc):
    result = []
    for _ in range(count):
        result.append(readFunc(file))
    return result


def read_chunk_array(self, file, chunkEnd, type, read_func):
    result = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == type:
            result.append(read_func(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return result


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


GEOMETRY_TYPE_SKIN = 0x00020000


def is_skin(mesh):
    return (mesh.header.attrs & GEOMETRY_TYPE_SKIN) > 0

#######################################################################################
# skeleton
#######################################################################################


def get_or_create_skeleton(hlod, hierarchy):
    rig = None

    if hlod == None or hlod.header.modelName == hlod.header.hierarchyName:
        return rig

    amtName = hierarchy.header.name

    for obj in bpy.data.objects:
        if obj.name == amtName:
            rig = obj

    if rig == None:
        rig = create_armature(hierarchy, amtName,
                              hlod.lodArray.subObjects)

    return rig


def make_transform_matrix(loc, rot):
    mat_loc = mathutils.Matrix.Translation(loc)
    mat_rot = mathutils.Quaternion(rot).to_matrix().to_4x4()
    return mat_loc @ mat_rot


def create_armature(hierarchy, amtName, subObjects):
    amt = bpy.data.armatures.new(hierarchy.header.name)
    amt.show_names = False

    rig = bpy.data.objects.new(amtName, amt)
    rig.location = hierarchy.header.centerPos
    rig.rotation_mode = 'QUATERNION'
    rig.track_axis = "POS_X"

    link_object_to_active_scene(rig)
    bpy.ops.object.mode_set(mode='EDIT')

    non_bone_pivots = []

    basic_sphere = create_sphere()

    for obj in subObjects:
        non_bone_pivots.append(hierarchy.pivots[obj.boneIndex])

    for pivot in hierarchy.pivots:
        if non_bone_pivots.count(pivot) > 0:
            continue

        bone = amt.edit_bones.new(pivot.name)
        matrix = make_transform_matrix(pivot.position, pivot.rotation)

        if pivot.parentID > 0:
            parent_pivot = hierarchy.pivots[pivot.parentID]
            bone.parent = amt.edit_bones[parent_pivot.name]
            matrix = bone.parent.matrix @ matrix

        bone.head = Vector((0.0, 0.0, 0.0))
        # has to point in y direction, so that the rotation is applied correctly
        bone.tail = Vector((0.0, 0.01, 0.0))
        bone.matrix = matrix

    bpy.ops.object.mode_set(mode='POSE')

    for bone in rig.pose.bones:
        bone.custom_shape = basic_sphere

    bpy.ops.object.mode_set(mode='OBJECT')

    return rig


#######################################################################################
# create material
#######################################################################################


def rgb_to_vector(rgb):
    return (rgb.r, rgb.g, rgb.b)


def create_vert_material(mesh, vertMat):
    mat = bpy.data.materials.new(mesh.header.meshName + "." + vertMat.vmName)
    mat.use_nodes = True
    principled = PrincipledBSDFWrapper(mat, is_readonly=False)
    principled.base_color = rgb_to_vector(vertMat.vmInfo.diffuse)
    principled.alpha = vertMat.vmInfo.opacity
    mat["Shininess"] = vertMat.vmInfo.shininess
    mat["Specular"] = rgb_to_vector(vertMat.vmInfo.specular)
    mat["Emission"] = rgb_to_vector(vertMat.vmInfo.emissive)
    mat["Diffuse"] = rgb_to_vector(vertMat.vmInfo.diffuse)
    mat["Translucency"] = vertMat.vmInfo.translucency
    return mat


def rgba_to_vector(prop):
    return (prop.value.r, prop.value.g, prop.value.b, prop.value.a)


def create_shader_materials(self, m, mesh):
    for material in m.shaderMaterials:
        mat = bpy.data.materials.new(m.header.meshName + ".ShaderMaterial")
        mat.use_nodes = True
        principled = PrincipledBSDFWrapper(mat, is_readonly=False)
        for prop in material.properties:
            if (prop.name == "DiffuseTexture"):
                principled.base_color_texture.image = load_texture(
                    self, prop.value)
            elif (prop.name == "NormalMap"):
                principled.normalmap_texture.image = load_texture(
                    self, prop.value)
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


def create_uvLayer(mesh, bm, tris, txCoords, ID=""):
    if len(txCoords) == 0:
        return

    uv_layer = mesh.uv_layers.new(name="texcoords" + ID, do_init=False)

    index = 0
    for f in bm.faces:
        tri = tris[index]
        for l in f.loops:
            idx = tri[l.index % 3]
            uv_layer.data[l.index].uv = txCoords[idx]
        index += 1


def create_uvlayers(mesh, tris, txCoords, txStages):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    create_uvLayer(mesh, bm, tris, txCoords)

    id = 0
    for stage in txStages:
        create_uvLayer(mesh, bm, tris, stage.txCoords, str(id))
        id += 1


#######################################################################################
# load texture
#######################################################################################

def load_texture(self, texName):
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


def load_texture_to_mat(self, texName, mat):
    img = load_texture(self, texName)
    principled = PrincipledBSDFWrapper(mat, is_readonly=False)
    principled.base_color_texture.image = img


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


def set_translation(bone, index, frame, value):
    bpy.context.scene.frame_set(frame)
    bone.location[index] = value
    bone.keyframe_insert(data_path='location', index=index, frame=frame)


def set_rotation(bone, frame, value):
    bone.rotation_mode = 'QUATERNION'
    bone.rotation_quaternion = value
    bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)


def set_transform(bone, channel, frame, value):
    if is_translation(channel):
        set_translation(bone, channel.type, frame, value)
    elif is_rotation(channel):
        set_rotation(bone, frame, value)


def apply_timecoded(bone, channel):
    for key in channel.timeCodes:
        set_transform(bone, channel, key.timeCode, key.value)


def apply_motionChannel_timeCoded(bone, channel):
    for d in channel.data:
        set_transform(bone, channel, d.timeCode, d.value)


def apply_motionChannel_adaptiveDelta(bone, channel):
    for i in range(channel.numTimeCodes):
        set_transform(bone, channel, i, channel.data.data[i])


def apply_uncompressed(bone, channel):
    for frame in range(channel.firstFrame, channel.lastFrame):
        data = channel.data[frame - channel.firstFrame]
        set_transform(bone, channel, frame, data)


def process_channels(hierarchy, channels, rig, apply_func):
    for channel in channels:
        if (channel.pivot == 0):
            continue  # skip roottransform

        pivot = hierarchy.pivots[channel.pivot]
        obj = get_bone(rig, pivot.name)

        apply_func(obj, channel)


def process_motion_channels(hierarchy, channels, rig):
    for channel in channels:
        if (channel.pivot == 0):
            continue  # skip roottransform

        pivot = hierarchy.pivots[channel.pivot]
        obj = get_bone(rig, pivot.name)

        if channel.deltaType == 0:
            apply_motionChannel_timeCoded(obj, channel)
        else:
            apply_motionChannel_adaptiveDelta(obj, channel)


def create_animation(self, animation, hierarchy, compressed):
    if animation == None:
        return

    rig = setup_animation(animation)

    if not compressed:
        process_channels(hierarchy, animation.channels,
                         rig, apply_uncompressed)
    else:
        process_channels(hierarchy, animation.timeCodedChannels,
                         rig, apply_timecoded)
        process_motion_channels(hierarchy, animation.motionChannels, rig)

    bpy.context.scene.frame_set(0)


def smooth_mesh(mesh):
    bpy.ops.object.mode_set(mode='OBJECT')

    for f in mesh.polygons:
        f.use_smooth = True

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
    if box == None:
        return

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
    b.display_type = 'WIRE'
    mat = bpy.data.materials.new("BOUNDINGBOX.Material")

    mat.diffuse_color = (box.color.r, box.color.g, box.color.b, 1.0)
    cube.materials.append(mat)
    b.location = box.center
    link_object_to_active_scene(b)
    cube.from_pydata(verts, [], faces)
    cube.update(calc_edges=True)
