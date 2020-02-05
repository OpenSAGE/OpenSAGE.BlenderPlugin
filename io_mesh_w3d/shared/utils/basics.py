# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy


def link_object_to_active_scene(obj, coll):
    coll.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def get_objects(type, object_list=None):  # MESH, ARMATURE
    if object_list is None:
        object_list = bpy.context.scene.objects
    return [object for object in object_list if object.type == type]