import bpy
import os
from . import w3d_structs

def load(givenfilepath, context, import_settings):
    """Start the w3d import"""
    print('Loading file', givenfilepath)

    file = open(givenfilepath,"rb")
    filesize = os.path.getsize(givenfilepath)


    return {'FINISHED'}