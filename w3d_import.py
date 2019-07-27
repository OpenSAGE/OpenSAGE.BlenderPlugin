import bpy

def load(givenfilepath, context, import_settings):
    """Start the w3d import"""
    print('Loading file', givenfilepath)
    return {'FINISHED'}