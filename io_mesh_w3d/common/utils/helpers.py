# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import os
from mathutils import Quaternion, Matrix
from bpy_extras.image_utils import load_image


def make_transform_matrix(loc, rot):
    mat_loc = Matrix.Translation(loc)
    mat_rot = Quaternion(rot).to_matrix().to_4x4()
    return mat_loc @ mat_rot


def get_objects(type, object_list=None):  # MESH, ARMATURE
    if object_list is None:
        object_list = bpy.context.scene.objects
    return [obj for obj in object_list if obj.type == type]


def switch_to_pose(rig, pose):
    if rig is not None:
        rig.data.pose_position = pose
        bpy.context.view_layer.update()


def insensitive_path(path):
    # find the io_stream on unix
    directory = os.path.dirname(path)
    name = os.path.basename(path)

    for io_stream_name in os.listdir(directory):
        if io_stream_name.lower() == name.lower():
            path = os.path.join(directory, io_stream_name)
    return path


def get_collection(hlod=None, index=''):
    if hlod is not None:
        name = hlod.model_name() + index
        if name in bpy.data.collections:
            return bpy.data.collections[name]
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
        return coll
    return bpy.context.scene.collection


def link_object_to_active_scene(obj, coll):
    coll.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def rig_object(obj, hierarchy, rig, sub_object):
    obj.parent = rig
    obj.parent_type = 'ARMATURE'
    if sub_object.bone_index <= 0:
        return

    pivot = hierarchy.pivots[sub_object.bone_index]

    obj.parent_bone = pivot.name
    obj.parent_type = 'BONE'


def get_or_create_uvlayer(context, mesh, b_mesh, triangles, mat_pass):
    tx_coords = None
    if mat_pass.tx_coords:
        tx_coords = mat_pass.tx_coords
    else:
        if mat_pass.tx_stages:
            if len(mat_pass.tx_stages[0].tx_coords) == 0:
                context.warning('texture stage did not have uv coordinates!')
                return
            tx_coords = mat_pass.tx_stages[0].tx_coords[0]
            if len(mat_pass.tx_stages[0].tx_coords) > 1:
                context.warning('only one set of texture coords per texture stage supported')
        if len(mat_pass.tx_stages) > 1:
            context.warning('only one texture stage per material pass supported')

    return create_uv_layer(mesh, b_mesh, triangles, tx_coords)

def create_uv_layer(mesh, b_mesh, triangles, tx_coords):
    if tx_coords is None:
        return

    uv_layer = mesh.uv_layers.new(do_init=False)
    for i, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            idx = triangles[i][loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx].xy

    return uv_layer.name


def find_texture(context, file, name=None):
    if name is None:
        name = file

    file = file.split('.', -1)[0]
    if name in bpy.data.images:
        return bpy.data.images[name]

    path = insensitive_path(os.path.dirname(context.filepath))
    filepath = path + os.path.sep + file
    extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']
    img = None
    for extension in extensions:
        img = load_image(filepath + extension)
        if img is not None:
            context.info('loaded texture: ' + filepath + extension)
            break

    if img is None:
        context.warning('texture not found: ' + filepath + ' ' + str(extensions))
        img = bpy.data.images.new(name, width=2048, height=2048)
        img.generated_type = 'COLOR_GRID'
        img.source = 'GENERATED'

    img.name = name
    img.alpha_mode = 'STRAIGHT'
    return img
