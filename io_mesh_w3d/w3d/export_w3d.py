# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.export_utils import *
from io_mesh_w3d.w3d.io_binary import STRING_LENGTH


def save(context, export_settings):
    print('Saving file :' + context.filepath + context.filename_ext)

    export_mode = export_settings['mode']
    print('export mode: ' + str(export_mode))

    if export_mode not in ['M', 'HM', 'HAM', 'H', 'A']:
        context.error('unsupported export mode: ' + export_mode + ', aborting export!')
        return {'CANCELLED'}

    container_name = os.path.basename(context.filepath)

    if len(container_name) > STRING_LENGTH:
        context.error('Filename is longer than ' + str(STRING_LENGTH) + ' characters, aborting export!')
        return {'CANCELLED'}

    (hierarchy, rig) = retrieve_hierarchy(context, container_name)
    hlod = create_hlod(hierarchy, container_name)
    boxes = retrieve_boxes(hierarchy, container_name)
    dazzles = retrieve_dazzles(hierarchy, container_name)

    if 'M' in export_mode:
        meshes = retrieve_meshes(context, hierarchy, rig, container_name)
        if not meshes:
            context.error('Scene does not contain any meshes, aborting export!')
            return {'CANCELLED'}

        for mesh in meshes:
            if not mesh.validate(context):
                context.error('aborting export!')
                return {'CANCELLED'}

    if 'H' in export_mode and not hierarchy.validate(context):
        context.error('aborting export!')
        return {'CANCELLED'}

    if export_mode in ['HM', 'HAM']:
        if not hlod.validate(context):
            context.error('aborting export!')
            return {'CANCELLED'}

        for box in boxes:
            if not box.validate(context):
                context.error('aborting export!')
                return {'CANCELLED'}

    if 'A' in export_mode:
        timecoded = export_settings['compression'] == 'TC'
        animation = retrieve_animation(
            container_name, hierarchy, rig, timecoded)
        if not animation.validate(context):
            context.error('aborting export!')
            return {'CANCELLED'}

    file = open(context.filepath + context.filename_ext, 'wb')

    if export_mode == 'M':
        if len(meshes) > 1:
            context.warning('Scene does contain multiple meshes, exporting only the first with export mode M!')
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

        for dazzle in dazzles:
            dazzle.write(file)

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
