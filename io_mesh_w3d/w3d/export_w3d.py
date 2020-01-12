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


    container_name = os.path.basename(self.filepath).split('.')[0]
    if bpy.context.scene.collection.children:
        container_name = bpy.context.scene.collection.children[0].name

    (hierarchy, rig) = retrieve_hierarchy(self, container_name)
    hlod = create_hlod(hierarchy, container_name)
    boxes = retrieve_boxes(hierarchy, hlod.header.model_name)

    if 'M' in export_mode:
        meshes = retrieve_meshes(self, hierarchy, rig, hlod.header.model_name)
        if not meshes:
            self.report({'ERROR'}, "Scene does not contain any meshes, aborting export!")
            return {'CANCELLED'}

    if 'A' in export_mode:
        timecoded = export_settings['w3d_compression'] == "TC"
        animation = retrieve_animation(container_name, hierarchy, rig, timecoded)
        channels = animation.time_coded_channels if timecoded else animation.channels
        if not channels:
            self.report({'ERROR'}, "Scene does not contain any animation data, aborting export!")
            return {'CANCELLED'}

    if export_mode == 'M':
        sknFile = open(self.filepath, "wb")
        if len(meshes) > 1:
            self.report({'WARNING'}, "Scene does contain multiple meshes, exporting only the first with export mode M!")
        meshes[0].header.container_name = ''
        meshes[0].write(sknFile)
        sknFile.close()
        return {'FINISHED'}

    elif export_mode == 'HM':
        sknFile = open(self.filepath, "wb")
        hierarchy.write(sknFile)

        for box in boxes:
            box.write(sknFile)

        for mesh in meshes:
            mesh.write(sknFile)

        hlod.write(sknFile)

        sknFile.close()

    elif export_mode == 'HAM':
        sknFile = open(self.filepath, "wb")
        hierarchy.write(sknFile)

        for box in boxes:
            box.write(sknFile)

        for mesh in meshes:
            mesh.write(sknFile)

        hlod.write(sknFile)

        animation.write(sknFile)

        sknFile.close()

    elif export_mode == 'H':
        if len(hierarchy.pivots) < 2:
            self.report({'ERROR'}, "Scene does not contain any hierarchy/skeleton data, aborting export!")
            return {'CANCELLED'}

        filename = os.path.splitext(os.path.basename(self.filepath))[0]
        sklFilePath = self.filepath.replace(
            filename, hierarchy.header.name.lower())

        sklFile = open(sklFilePath, "wb")
        hierarchy.write(sklFile)
        sklFile.close()

    elif export_mode == 'A':
        aniFile = open(self.filepath, "wb")
        animation.write(aniFile)
        aniFile.close()

    else:
        message = "WARNING: unsupported export mode: %s" % export_mode
        print(message)
        self.report({'ERROR'}, message)
        return {'CANCELLED'}

    return {'FINISHED'}
