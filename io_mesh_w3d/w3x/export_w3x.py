# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.export_utils import *
from io_mesh_w3d.w3x.structs.include import *
import os


def save(context, export_settings, data_context):
    filepath = context.filepath
    if not filepath.lower().endswith(context.filename_ext):
        filepath += context.filename_ext

    filepath_pure = os.path.splitext(filepath)[0]
    directory = os.path.dirname(filepath) + os.path.sep

    # context.info(f'Saving file: {filepath}')

    export_mode = export_settings['mode']
    # context.info(f'export mode: {export_mode}')

    root = create_root()
    # includes = create_node(root, 'Includes')

    # directory = os.path.dirname(context.filepath) + os.path.sep

    if 'H' in export_mode and data_context.hierarchy:
        if export_settings['individual_files']:
            path = filepath_pure + "_SKL" + context.filename_ext
            context.info('Saving file :' + path)
            write_struct(data_context.hierarchy, path)
        else:
            data_context.hierarchy.create(root)
            
    if 'M' in export_mode:
        # obbox
        for box in data_context.collision_boxes:
            if export_settings['individual_files']:
                path = directory + box.identifier() + context.filename_ext
                context.info('Saving file :' + path)
                write_struct(box, path)
            else:
                box.create(root)
        # w3dmesh
        for mesh in data_context.meshes:
            if export_settings['individual_files']:
                path = directory + mesh.identifier() + context.filename_ext
                context.info('Saving file :' + path)
                write_struct(mesh, path)
            else:
                mesh.create(root)
        # w3dcontainer
        if data_context.hlod:
            if export_settings['individual_files']:
                    path = filepath_pure + "_CTR" + context.filename_ext
                    context.info('Saving file :' + path)
                    write_struct(data_context.hlod, path)
            else:
                data_context.hlod.create(root)

    if "A" in export_mode and data_context.animation:
        if export_settings['individual_files']:
            path = directory + data_context.animation.name() + context.filename_ext
            context.info('Saving file :' + path)
            write_struct(data_context.animation, path)
        else:
            data_context.animation.create(root)

    if export_settings['create_texture_xmls']:
        tex_path = directory + "Texture.xml"
        context.info('Saving file :' + tex_path)
        tex_root = create_root()
        for t, f in data_context.textures:
            tex = Texture(id=t, file=f)
            tex.create(tex_root)
        write(tex_root, tex_path)

    if not export_settings['individual_files']:
        context.info('Saving file :' + filepath)
        write(root, filepath)

    if not data_context.hierarchy:
        context.warning('Export incomplete')

    return {'FINISHED'}
