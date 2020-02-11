# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bmesh
import bpy
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.structs.data_context import *

from io_mesh_w3d.common.utils.mesh_export import *
from io_mesh_w3d.common.utils.hierarchy_export import *
from io_mesh_w3d.common.utils.animation_export import *
from io_mesh_w3d.common.utils.hlod_export import *
from io_mesh_w3d.common.utils.box_export import *
from io_mesh_w3d.w3d.utils.dazzle_export import *


def save(context, export_settings):
    data_context = DataContext(
        container_name='',
        rig=None,
        meshes=[],
        textures=[],
        collision_boxes=[],
        dazzles=[],
        hierarchy=None,
        hlod=None)

    if not retrieve_data(context, export_settings, data_context):
        return {'CANCELLED'}

    if context.file_format == 'W3X':
        context.filename_ext = '.w3x'
        from .w3x.export_w3x import save
        return save(context, export_settings, data_context)

    context.filename_ext = '.w3d'
    from .w3d.export_w3d import save
    return save(context, export_settings, data_context)


def retrieve_data(context, export_settings, data_context):
    export_mode = export_settings['mode']

    if export_mode not in ['M', 'HM', 'HAM', 'H', 'A']:
        context.error('unsupported export mode: ' + export_mode + ', aborting export!')
        return False

    data_context.container_name = os.path.basename(context.filepath)

    if context.file_format == 'W3D' and len(data_context.container_name) > STRING_LENGTH:
        context.error('Filename is longer than ' + str(STRING_LENGTH) + ' characters, aborting export!')
        return False

    (hierarchy, rig) = retrieve_hierarchy(context, data_context.container_name)
    data_context.hierarchy = hierarchy
    data_context.rig = rig
    data_context.hlod = create_hlod(hierarchy, data_context.container_name)
    data_context.collision_boxes = retrieve_boxes(data_context.container_name)
    data_context.dazzles = retrieve_dazzles(data_context.container_name)

    if 'M' in export_mode:
        (meshes, textures) = retrieve_meshes(context, hierarchy, rig, data_context.container_name)
        data_context.meshes = meshes
        data_context.textures = textures
        if not data_context.meshes:
            context.error('Scene does not contain any meshes, aborting export!')
            return False

        for mesh in data_context.meshes:
            if not mesh.validate(context):
                context.error('aborting export!')
                return False

    if 'H' in export_mode and not hierarchy.validate(context):
        context.error('aborting export!')
        return False

    if export_mode in ['HM', 'HAM']:
        if not data_context.hlod.validate(context):
            context.error('aborting export!')
            return False

        for box in data_context.collision_boxes:
            if not box.validate(context):
                context.error('aborting export!')
                return False

    if 'A' in export_mode:
        timecoded = export_settings['compression'] == 'TC'
        data_context.animation = retrieve_animation(
            data_context.container_name, hierarchy, rig, timecoded)
        if not data_context.animation.validate(context):
            context.error('aborting export!')
            return False
    return True
