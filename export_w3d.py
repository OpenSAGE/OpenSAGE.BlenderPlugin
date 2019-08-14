# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

import bpy


def save(givenfilepath, context, export_settings):
    """Start the w3d export and save to a .w3d file."""
    print('Saving file', givenfilepath)
    return {'FINISHED'}
