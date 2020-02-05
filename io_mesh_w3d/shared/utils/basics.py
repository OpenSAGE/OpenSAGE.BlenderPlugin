# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import os

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


def get_objects(type, object_list=None):  # MESH, ARMATURE
    if object_list is None:
        object_list = bpy.context.scene.objects
    return [object for object in object_list if object.type == type]