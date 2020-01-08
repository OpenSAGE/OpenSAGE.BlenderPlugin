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

    container_name = None
    for coll in bpy.data.collections:


    hlod = create_hlod(hierarchy)
    (hierarchy, rig) = retrieve_hierarchy(self, hlod.header.model_name)

    if export_mode == 'M':
        meshes = retrieve_meshes(self, hierarchy, rig, hlod.header.model_name)
        if not meshes:
            self.report({'ERROR'}, "Scene does not contain any meshes, aborting export!")
            return {'CANCELLED'}

        sknFile = open(self.filepath, "wb")

        print(hlod.header.model_name + " " + hlod.header.hierarchy_name)
        if hlod and hlod.header.model_name == hlod.header.hierarchy_name:
            if len(hierarchy.pivots) > 1:
                hierarchy.write(sknFile)

            timecoded = False
            compressionMode = export_settings['w3d_compression']

            if compressionMode == "TC":
                timecoded = True

            animation = retrieve_animation(
                containerName, hierarchy, rig, timecoded)

            channels = animation.time_coded_channels if timecoded else animation.channels
            if channels:
                animation.write(sknFile)

        boxes = retrieve_boxes(hierarchy, hlod.header.model_name)
        for box in boxes:
            box.write(sknFile)

        for mesh in meshes:
            mesh.write(sknFile)

        if hlod.lod_arrays:
            hlod.write(sknFile)

        sknFile.close()

    elif export_mode == 'H':
        if len(hierarchy.pivots) < 2:
            self.report({'ERROR'}, "Scene does not contain any hierarchy data, aborting export!")
            return {'CANCELLED'}

        if hlod and hlod.header.model_name == hlod.header.hierarchy_name:
            self.report({'ERROR'}, "Armature is named the same as collection -> use export mode 'M' instead, aborting export!")
            return {'CANCELLED'}

        filename = os.path.splitext(os.path.basename(self.filepath))[0]
        sklFilePath = self.filepath.replace(
            filename, hierarchy.header.name.lower())

        sklFile = open(sklFilePath, "wb")
        hierarchy.write(sklFile)
        sklFile.close()

    elif export_mode == 'A':
        timecoded = False
        if export_settings['w3d_compression'] == "TC":
            timecoded = True

        animation = retrieve_animation(
            containerName, hierarchy, rig, timecoded)

        channels = animation.time_coded_channels if timecoded else animation.channels
        if not channels:
            self.report({'ERROR'}, "Scene does not contain any animation data, aborting export!")
            return {'CANCELLED'}

        if hlod and hlod.header.model_name == hlod.header.hierarchy_name:
            self.report({'ERROR'}, "Armature is named the same as collection -> use export mode 'M' instead, aborting export!")
            return {'CANCELLED'}

        aniFile = open(self.filepath, "wb")
        animation.write(aniFile)
        aniFile.close()

    else:
        message = "WARNING: unsupported export mode: %s" % export_mode
        print(message)
        self.report({'ERROR'}, message)
        return {'CANCELLED'}

    return {'FINISHED'}
