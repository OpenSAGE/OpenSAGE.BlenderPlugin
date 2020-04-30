import bpy

bpy.ops.preferences.addon_install(file_path='', overwrite=True)
bpy.ops.preferences.addon_enable(module='Import/Export Westwood W3D Format (.w3d/.w3x)')