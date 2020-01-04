# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bpy

from io_mesh_w3d.export_utils import *


def save(self, export_settings):
    print('Saving file', self.filepath)

    export_mode = export_settings['w3d_mode']
    print("export mode: " + str(export_mode))

    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except BaseException:
        print("could not set mode to OBJECT")

    containerName = (os.path.splitext(
        os.path.basename(self.filepath))[0]).upper()

    (hierarchy, rig) = retrieve_hierarchy(containerName)

    hlod = create_hlod(containerName, hierarchy.header.name)

    if export_mode in ('M', 'HAM'):
        sknFile = open(self.filepath, "wb")

        boxes = retrieve_boxes(hlod, hierarchy)
        for box in boxes:
            box.write(sknFile)

        meshes = retrieve_meshes(self, hierarchy, rig, hlod, containerName)
        for mesh in meshes:
            mesh.write(sknFile)

        hlod.lod_arrays[0].header.model_count = len(hlod.lod_arrays[0].sub_objects)
        hlod.write(sknFile)

        if export_mode == 'HAM':
            hierarchy.write(sknFile)
        sknFile.close()

    elif export_mode == 'H':
        filename = os.path.splitext(os.path.basename(self.filepath))[0]
        sklFilePath = self.filepath.replace(
            filename, hierarchy.header.name.lower())
        sklFile = open(sklFilePath, "wb")
        hierarchy.write(sklFile)
        sklFile.close()

    elif export_mode == 'A':
        aniFile = open(self.filepath, "wb")
        timecoded = False
        compressionMode = export_settings['w3d_compression']

        if compressionMode == "TC":
            timecoded = True

        animation = retrieve_animation(
            containerName, hierarchy, rig, timecoded)
        animation.write(aniFile)
        aniFile.close()

    else:
        message = "WARNING: unsupported export mode: %s" % export_mode
        print(message)
        self.report({'ERROR'}, message)

    return {'FINISHED'}
