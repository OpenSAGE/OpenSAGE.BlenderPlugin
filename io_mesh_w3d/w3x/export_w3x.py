# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.export_utils import *
from io_mesh_w3d.w3x.structs.include import *


def save(context, export_settings, data_context):
    context.info('Saving file :' + context.filepath + context.filename_ext)

    export_mode = export_settings['mode']
    context.info("export mode: " + str(export_mode))

    root = create_root()
    includes = create_node(root, 'Includes')

    if export_mode == 'M':
        if len(data_context.meshes) > 1:
            context.warning('Scene does contain multiple meshes, exporting only the first with export mode M!')
        data_context.meshes[0].header.container_name = ''
        data_context.meshes[0].header.mesh_name = data_context.container_name
        data_context.meshes[0].create(root)

    elif export_mode == 'HM' or export_mode == 'HAM':
        if export_mode == 'HAM':
            data_context.hierarchy.create(root)

        if export_settings['use_existing_skeleton']:
            hierarchy_include = Include(type='all', source='ART:' + data_context.hierarchy.name() + '.w3x')
            hierarchy_include.create(includes)

        dir = os.path.dirname(context.filepath) + os.path.sep

        if export_settings['create_texture_xmls']:
            for texture in data_context.textures:
                id = texture.split('.')[0]
                path = dir + id + '.xml'
                context.info('Saving file :' + path)
                write_struct(Texture(id=id, file=texture), path)

        if export_settings['individual_files']:
            hierarchy_include = Include(type='all', source='ART:' + data_context.hierarchy.name() + '.w3x')
            hierarchy_include.create(includes)
            if not export_settings['use_existing_skeleton']:
                path = dir + data_context.hierarchy.name() + context.filename_ext
                context.info('Saving file :' + path)
                write_struct(data_context.hierarchy, path)

            for box in data_context.collision_boxes:
                box_include = Include(type='all', source='ART:' + box.name_ + '.w3x')
                box_include.create(includes)
                path = dir + box.name_ + context.filename_ext
                context.info('Saving file :' + path)
                write_struct(box, path)

            for mesh in data_context.meshes:
                mesh_include = Include(type='all', source='ART:' + mesh.identifier() + '.w3x')
                mesh_include.create(includes)
                path = dir + mesh.identifier() + context.filename_ext
                context.info('Saving file :' + path)
                write_struct(mesh, path)

        else:
            for texture in data_context.textures:
                id = texture.split('.')[0]
                texture_include = Include(type='all', source='ART:' + id + '.xml')
                texture_include.create(includes)

            for box in data_context.collision_boxes:
                box.create(root)

            for mesh in data_context.meshes:
                mesh.create(root)

        data_context.hlod.create(root)

        if export_mode == 'HAM':
            data_context.animation.header.hierarchy_name = data_context.container_name
            data_context.animation.create(root)

    elif export_mode == 'A':
        hierarchy_include = Include(type='all', source='ART:' + data_context.hierarchy.header.name + '.w3x')
        hierarchy_include.create(includes)
        data_context.animation.create(root)

    elif export_mode == 'H':
        data_context.hierarchy.header.name = data_context.container_name
        data_context.hierarchy.create(root)

    else:
        context.error('unsupported export mode: ' + export_mode + ', aborting export!')
        return {'CANCELLED'}

    write(root, context.filepath + context.filename_ext)

    context.info('finished')
    return {'FINISHED'}
