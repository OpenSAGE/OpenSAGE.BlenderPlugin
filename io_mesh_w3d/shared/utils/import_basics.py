# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import os
from bpy_extras.image_utils import load_image


def insensitive_path(path):
    # find the io_stream on unix
    directory = os.path.dirname(path)
    name = os.path.basename(path)

    for io_streamname in os.listdir(directory):
        if io_streamname.lower() == name.lower():
            path = os.path.join(directory, io_streamname)
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


def rig_object(object, hierarchy, rig, sub_object):
    if hierarchy is None or not sub_object or sub_object.bone_index <= 0:
        return

    pivot = hierarchy.pivots[sub_object.bone_index]

    if rig is not None and pivot.name in rig.pose.bones:
        object.parent = rig
        object.parent_bone = pivot.name
        object.parent_type = 'BONE'
        return

    object.rotation_mode = 'QUATERNION'
    object.delta_location = pivot.translation
    object.delta_rotation_quaternion = pivot.rotation

    if pivot.parent_id <= 0:
        return

    parent_pivot = hierarchy.pivots[pivot.parent_id]

    if parent_pivot.name in bpy.data.objects:
        object.parent = bpy.data.objects[parent_pivot.name]
    elif rig is not None and parent_pivot.name in rig.pose.bones:
        object.parent = rig
        object.parent_bone = parent_pivot.name
        object.parent_type = 'BONE'


def create_uvlayer(context, mesh, b_mesh, tris, mat_pass):
    tx_coords = None
    if mat_pass.tx_coords:
        tx_coords = mat_pass.tx_coords
    else:
        if len(mat_pass.tx_stages) > 0:
            tx_coords = mat_pass.tx_stages[0].tx_coords
        if len(mat_pass.tx_stages) > 1:
            context.warning('only one texture stage per material pass supported on export')

    if not tx_coords:
        return

    uv_layer = mesh.uv_layers.new(do_init=False)
    for i, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            idx = tris[i][loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx].xy


def find_texture(context, file, name=None):
    if name is None:
        name = file

    file = file.split('.', -1)[0]
    if name in bpy.data.images:
        return bpy.data.images[name]

    path = insensitive_path(os.path.dirname(context.filepath))
    filepath = path + os.path.sep + file
    extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']
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
