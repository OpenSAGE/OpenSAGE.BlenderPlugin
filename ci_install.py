import bpy

result = bpy.ops.preferences.addon_install(filepath='../../io_mesh_w3d.zip', overwrite=True)
if result is not 'FINISHED':
	raise Exception(1)

result = bpy.ops.preferences.addon_enable(module='io_mesh_w3d')
if result is not 'FINISHED':
	raise Exception(1)
