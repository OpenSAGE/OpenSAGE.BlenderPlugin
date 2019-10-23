# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import os
import bpy

from io_mesh_w3d.export_utils_w3d import *


def save(givenfilepath, _context, export_settings):
    """Start the w3d export and save to a .w3d file."""
    print('Saving file', givenfilepath)

    export_mode = export_settings['w3d_mode']
    print("export mode: " + str(export_mode))

    bpy.ops.object.mode_set(mode='OBJECT')

    containerName = (os.path.splitext(
        os.path.basename(givenfilepath))[0]).upper()

    (hierarchy, rig) = retrieve_hierarchy(containerName)

    hlod = HLod()
    hlod.header.model_name = containerName
    hlod.header.hierarchy_name = hierarchy.header.name
    hlod.lod_array.sub_objects = []

    if export_mode in ('M', 'HAM'):
        sknFile = open(givenfilepath, "wb")

        boxes = retrieve_boxes(hlod)
        for box in boxes:
            box.write(sknFile)

        meshes = retrieve_meshes(sknFile, hierarchy, rig, hlod, containerName)
        for mesh in meshes:
            mesh.write(sknFile)

        hlod.lod_array.header.model_count = len(hlod.lod_array.sub_objects)
        hlod.write(sknFile)

        if export_mode == 'HAM':
            hierarchy.write(sknFile)
        sknFile.close()

    elif export_mode == 'H':
        filename = os.path.splitext(os.path.basename(givenfilepath))[0]
        sklFilePath = givenfilepath.replace(filename, hierarchy.header.name.lower())
        sklFile = open(sklFilePath, "wb")
        hierarchy.write(sklFile)
        sklFile.close()

    elif export_mode == 'A':
        aniFile = open(givenfilepath, "wb")
        export_animation(aniFile, containerName, hierarchy)
        aniFile.close()

    return {'FINISHED'}
