# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

import bpy
from io_mesh_w3d.export_utils_w3d import *


def save(givenfilepath, context, export_settings):
    """Start the w3d export and save to a .w3d file."""
    print('Saving file', givenfilepath)

    export_mode = export_settings['w3d_mode']
    print ("export mode:" + str(export_mode))

    #check for the export settings
    bpy.ops.object.mode_set(mode='OBJECT')


    if export_mode == 'M' or export_mode == 'HAM':
        export_meshes(givenfilepath)

    return {'FINISHED'}
