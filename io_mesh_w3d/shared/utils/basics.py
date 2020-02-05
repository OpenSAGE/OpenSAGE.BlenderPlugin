# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy


def get_objects(type, object_list=None):  # MESH, ARMATURE
    if object_list is None:
        object_list = bpy.context.scene.objects
    return [object for object in object_list if object.type == type]
