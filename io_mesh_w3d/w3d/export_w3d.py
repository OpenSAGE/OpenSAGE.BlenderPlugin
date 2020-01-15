# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.export_utils import *


def save(self, export_settings):
    print('Saving file :' + self.filepath)

    export_mode = export_settings['mode']
    print("export mode: " + str(export_mode))

    if not export_mode in ['M', 'HM', 'HAM', 'H', 'A']:
        message = "WARNING: unsupported export mode: " + export_mode
        print(message)
        self.report({'ERROR'}, message)
        return {'CANCELLED'}

    container_name = os.path.basename(self.filepath).split('.')[0]

    (hierarchy, rig) = retrieve_hierarchy(self, container_name)
    hlod = create_hlod(hierarchy, container_name)
    boxes = retrieve_boxes(hierarchy, container_name)

    if 'M' in export_mode:
        meshes = retrieve_meshes(self, hierarchy, rig, container_name)
        if not meshes:
            self.report(
                {'ERROR'}, "Scene does not contain any meshes, aborting export!")
            return {'CANCELLED'}

    if 'A' in export_mode:
        timecoded = export_settings['compression'] == "TC"
        animation = retrieve_animation(
            container_name, hierarchy, rig, timecoded)
        channels = animation.time_coded_channels if timecoded else animation.channels
        if not channels:
            self.report(
                {'ERROR'}, "Scene does not contain any animation data, aborting export!")
            return {'CANCELLED'}

    if export_mode == 'HM' or export_mode == 'HAM':
        if not check_hlod_sub_object_names(self, hlod):
            return {'CANCELLED'}

    if export_mode == 'H':
        if len(hierarchy.pivots) < 2:
            self.report(
                {'ERROR'}, "Scene does not contain any hierarchy/skeleton data, aborting export!")
            return {'CANCELLED'}

    file = open(self.filepath, "wb")

    if export_mode == 'M':
        if len(meshes) > 1:
            self.report(
                {'WARNING'}, "Scene does contain multiple meshes, exporting only the first with export mode M!")
        meshes[0].header.container_name = ''
        meshes[0].header.mesh_name = container_name
        meshes[0].write(file)

    elif export_mode == 'HM' or export_mode == 'HAM':
        if export_mode == 'HAM' \
                or not export_settings['use_existing_skeleton']:
            hierarchy.header.name = container_name
            hlod.header.hierarchy_name = container_name
            hierarchy.write(file)

        for box in boxes:
            box.write(file)

        for mesh in meshes:
            mesh.write(file)

        hlod.write(file)
        if export_mode == 'HAM':
            animation.header.hierarchy_name = container_name
            animation.write(file)

    elif export_mode == 'A':
        animation.write(file)

    elif export_mode == 'H':
        hierarchy.header.name = container_name
        hierarchy.write(file)

    file.close()
    return {'FINISHED'}
