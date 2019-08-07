# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import os
import bpy
import bmesh

from mathutils import Vector, Quaternion

from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.image_utils import load_image

#######################################################################################
# helper methods
#######################################################################################


def InsensitiveOpen(path):
    #find the file on unix
    dir = os.path.dirname(path)
    name = os.path.basename(path)

    for filename in os.listdir(dir):
        if filename.lower() == name.lower():
            path = os.path.join(dir, filename)
            return open(path, "rb")


def InsensitivePath(path):
     #find the file on unix
    dir = os.path.dirname(path)
    name = os.path.basename(path)

    for filename in os.listdir(dir):
        if filename.lower() == name.lower():
            path = os.path.join(dir, filename)
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
# create armature
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
    bpy.ops.object.mode_set(mode='EDIT')

    non_bone_pivots = []

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
        bone.tail = Vector((0.0, 1.0, 0.0))

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

    bpy.ops.object.mode_set(mode='OBJECT')

    return rig


#######################################################################################
# create material
#######################################################################################

def create_material(mesh, vertMat):
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

#######################################################################################
# create uvlayer
#######################################################################################


def create_uvlayer(mesh, tris, matPass):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    uv_layer = mesh.uv_layers.new(name="texcoords", do_init=False)

    index = 0
    if len(matPass.txStage.txCoords) > 0:
        for f in bm.faces:
            tri = tris[index]
            for l in f.loops:
                idx = tri[l.index % 3]
                uv_layer.data[l.index].uv = matPass.txStage.txCoords[idx]
            index += 1


#######################################################################################
# load texture
#######################################################################################

def load_texture(self, mesh, texName, tex_type, destBlend):
    script_directory = os.path.dirname(os.path.abspath(__file__))

    found_img = False
    basename = os.path.splitext(texName)[0]

    # Test if the image file already exists
    for image in bpy.data.images:
        if basename == os.path.splitext(image.name)[0]:
            img = image
            found_img = True
            print("Found an existing image")

    # Try to load the image file
    if found_img == False:
        tgapath = os.path.dirname(self.filepath) + "/" + basename + ".tga"
        ddspath = os.path.dirname(self.filepath) + "/" + basename + ".dds"
        tgapath = InsensitivePath(tgapath)
        ddspath = InsensitivePath(ddspath)

        print("Trying tga: " + tgapath)
        img = load_image(tgapath)

        if img == None:
            print("Trying dds: " + ddspath)
            img = load_image(ddspath)

    # Set the image as input to our node material
    mat = mesh.materials[0]
    principled = PrincipledBSDFWrapper(mat, is_readonly=False)
    principled.base_color_texture.image = img
