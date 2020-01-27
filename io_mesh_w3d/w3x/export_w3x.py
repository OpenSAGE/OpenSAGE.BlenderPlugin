# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.export_utils import *
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.w3x.structs.include import *


def save(context, export_settings):
    print('Saving file :' + context.filepath)

    export_mode = export_settings['mode']
    print("export mode: " + str(export_mode))

    if export_mode not in ['M', 'HM', 'HAM', 'H', 'A']:
        context.error('unsupported export mode: ' + export_mode + ', aborting export!')
        return {'CANCELLED'}

    container_name = os.path.basename(context.filepath).split('.')[0]

    (hierarchy, rig) = retrieve_hierarchy(context, container_name)
    hlod = create_hlod(hierarchy, container_name)
    boxes = retrieve_boxes(hierarchy, container_name)

    if 'M' in export_mode:
        (meshes, textures) = retrieve_meshes(context, hierarchy, rig, container_name, w3x=True)
        if not meshes:
            context.error('Scene does not contain any meshes, aborting export!')
            return {'CANCELLED'}

        for mesh in meshes:
            if not mesh.validate(context, w3x=True):
                context.error('aborting export!')
                return {'CANCELLED'}

    if 'H' in export_mode and not hierarchy.validate(context, w3x=True):
        context.error('aborting export!')
        return {'CANCELLED'}

    if export_mode in ['HM', 'HAM']:
        if not hlod.validate(context, w3x=True):
            context.error('aborting export!')
            return {'CANCELLED'}

        for box in boxes:
            if not box.validate(context, w3x=True):
                context.error('aborting export!')
                return {'CANCELLED'}

    if 'A' in export_mode:
        timecoded = export_settings['compression'] == "TC"
        animation = retrieve_animation(
            container_name, hierarchy, rig, timecoded)
        if not animation.validate(context, w3x=True):
            context.error('aborting export!')
            return {'CANCELLED'}

    doc = minidom.Document()
    asset = create_asset_declaration(doc)
    includes = doc.createElement('Includes')
    asset.appendChild(includes)

    if export_mode == 'M':
        if len(meshes) > 1:
            context.warning('Scene does contain multiple meshes, exporting only the first with export mode M!')
        meshes[0].header.container_name = ''
        meshes[0].header.mesh_name = container_name
        asset.appendChild(meshes[0].create(doc))

    elif export_mode == 'HM' or export_mode == 'HAM':
        if export_mode == 'HAM' \
                or not export_settings['use_existing_skeleton']:
            hierarchy.header.name = container_name
            hlod.header.hierarchy_name = container_name
            asset.appendChild(hierarchy.create(doc))
        else:
            hierarchy_include = Include(type='all', source='ART:' + hierarchy.header.name + '.w3x')
            includes.appendChild(hierarchy_include.create(doc))

        for texture in textures:
            id = texture.split('.')[0]
            texture_include = Include(type='all', source='ART:' + id + '.xml')
            includes.appendChild(texture_include.create(doc))

        for box in boxes:
            asset.appendChild(box.create(doc))

        for mesh in meshes:
            asset.appendChild(mesh.create(doc))

        asset.appendChild(hlod.create(doc))
        if export_mode == 'HAM':
            animation.header.hierarchy_name = container_name
            asset.appendChild(animation.create(doc))

    elif export_mode == 'A':
        hierarchy_include = Include(type='all', source='ART:' + hierarchy.header.name + '.w3x')
        includes.appendChild(hierarchy_include.create(doc))
        asset.appendChild(animation.create(doc))

    elif export_mode == 'H':
        hierarchy.header.name = container_name
        asset.appendChild(hierarchy.create(doc))

    doc.appendChild(asset)

    file = open(context.filepath, "wb")
    file.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
    file.close()

    # create texture xml files
    if export_mode == 'HM' or export_mode == 'HAM' and export_settings['create_texture_xmls']:
        print('creating files')
        directory = os.path.dirname(context.filepath)
        print(directory)
        for texture in textures:
            id = texture.split('.')[0]
            doc = minidom.Document()
            asset = create_asset_declaration(doc)
            asset.appendChild(Texture(id=id, file=texture).create(doc))
            doc.appendChild(asset)

            file = open(directory + '/' + id + '.xml', "wb")
            file.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
            file.close()

    print('finished')
    return {'FINISHED'}
