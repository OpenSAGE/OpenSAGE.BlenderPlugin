# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.export_utils import *
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.w3x.structs.include import *


def save(context, export_settings, data_context):
    context.info('Saving file :' + context.filepath + context.filename_ext)

    export_mode = export_settings['mode']
    context.info("export mode: " + str(export_mode))

    doc = minidom.Document()
    asset = create_asset_declaration(doc)
    includes = doc.createElement('Includes')
    asset.appendChild(includes)

    if export_mode == 'M':
        if len(data_context.meshes) > 1:
            context.warning('Scene does contain multiple meshes, exporting only the first with export mode M!')
        data_context.meshes[0].header.container_name = ''
        data_context.meshes[0].header.mesh_name = data_context.container_name
        asset.appendChild(data_context.meshes[0].create(doc))

    elif export_mode == 'HM' or export_mode == 'HAM':
        if export_mode == 'HAM' \
                or not export_settings['use_existing_skeleton']:
            data_context.hierarchy.header.name = data_context.container_name
            data_context.hlod.header.hierarchy_name = data_context.container_name
            asset.appendChild(data_context.hierarchy.create(doc))

        elif not export_settings['individual_files']:
            hierarchy_include = Include(type='all', source='ART:' + data_context.hierarchy.header.name + '.w3x')
            includes.appendChild(hierarchy_include.create(doc))

        if export_settings['individual_files']:
            dir = os.path.dirname(context.filepath)

            write_struct_to_file(
                data_context.hierarchy,
                dir +
                os.path.sep +
                data_context.hierarchy.name() +
                context.filename_ext)

            for box in data_context.boxes:
                write_struct_to_file(box, dir + os.path.sep + box.name_ + context.filename_ext)

            for mesh in data_context.meshes:
                write_struct_to_file(mesh, dir + os.path.sep + mesh.identifier() + context.filename_ext)

        else:
            for texture in data_context.textures:
                id = texture.split('.')[0]
                texture_include = Include(type='all', source='ART:' + id + '.xml')
                includes.appendChild(texture_include.create(doc))

            for box in data_context.boxes:
                asset.appendChild(box.create(doc))

            for mesh in data_context.meshes:
                asset.appendChild(mesh.create(doc))

        asset.appendChild(data_context.hlod.create(doc))

        if export_mode == 'HAM':
            data_context.animation.header.hierarchy_name = data_context.container_name
            asset.appendChild(data_context.animation.create(doc))

    elif export_mode == 'A':
        hierarchy_include = Include(type='all', source='ART:' + data_context.hierarchy.header.name + '.w3x')
        includes.appendChild(hierarchy_include.create(doc))
        asset.appendChild(data_context.animation.create(doc))

    elif export_mode == 'H':
        data_context.hierarchy.header.name = data_context.container_name
        asset.appendChild(data_context.hierarchy.create(doc))

    doc.appendChild(asset)

    file = open(context.filepath + context.filename_ext, "wb")
    file.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
    file.close()

    # create texture xml files
    if (export_mode == 'HM' or export_mode == 'HAM') and export_settings['create_texture_xmls']:
        dir = os.path.dirname(context.filepath)

        for texture in data_context.textures:
            id = texture.split('.')[0]
            write_struct_to_file(Texture(id=id, file=texture), dir + os.path.sep + id + '.xml')

    context.info('finished')
    return {'FINISHED'}
