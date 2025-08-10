# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.common.structs.collision_box import *
from io_mesh_w3d.common.structs.data_context import *
from io_mesh_w3d.common.structs.hierarchy import *
from io_mesh_w3d.common.structs.hlod import *
from io_mesh_w3d.common.structs.mesh import *
from io_mesh_w3d.w3d.structs.dazzle import *
from io_mesh_w3d.w3d.structs.compressed_animation import *


def load_file(context, data_context, path=None):
    if path is None:
        path = context.filepath

    path = insensitive_path(path)
    context.info(f'Loading file: {path}')

    if not os.path.exists(path):
        context.error(f'file not found: {path}')
        return

    file = open(path, 'rb')
    filesize = os.path.getsize(path)

    while file.tell() < filesize:
        chunk_type, chunk_size, chunk_end = read_chunk_head(file)

        if chunk_type == W3D_CHUNK_MESH:
            data_context.meshes.append(W3DMesh.read(context, file, chunk_end))
        elif chunk_type == W3D_CHUNK_HIERARCHY:
            if data_context.hierarchy is None:
                data_context.hierarchy = Hierarchy.read(context, file, chunk_end)
            else:
                context.warning('-> already got one hierarchy chunk (skipping this one)!')
                file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_HLOD:
            if data_context.hlod is None:
                data_context.hlod = HLod.read(context, file, chunk_end)
            else:
                context.warning('-> already got one hlod chunk (skipping this one)!')
                file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_ANIMATION:
            if data_context.animation is None and data_context.compressed_animation is None:
                data_context.animation = Animation.read(context, file, chunk_end)
            else:
                context.warning('-> already got one animation chunk (skipping this one)!')
                file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION:
            if data_context.animation is None and data_context.compressed_animation is None:
                data_context.compressed_animation = CompressedAnimation.read(context, file, chunk_end)
            else:
                context.warning('-> already got one animation chunk (skipping this one)!')
                file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_BOX:
            data_context.collision_boxes.append(CollisionBox.read(file))
        elif chunk_type == W3D_CHUNK_DAZZLE:
            data_context.dazzles.append(Dazzle.read(context, file, chunk_end))
        elif chunk_type == W3D_CHUNK_MORPH_ANIMATION:
            context.info('-> morph animation chunk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_HMODEL:
            context.info('-> hmodel chnuk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LODMODEL:
            context.info('-> lodmodel chunk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_COLLECTION:
            context.info('-> collection chunk not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_POINTS:
            context.info('-> points chunk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LIGHT:
            context.info('-> light chunk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_EMITTER:
            context.info('-> emitter chunk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_AGGREGATE:
            context.info('-> aggregate chunk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_NULL_OBJECT:
            context.info('-> null object chunkt is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LIGHTSCAPE:
            context.info('-> lightscape chunk is not supported')
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_SOUNDROBJ:
            context.info('-> soundobj chunk is not supported')
            file.seek(chunk_size, 1)
        else:
            skip_unknown_chunk(context, file, chunk_type, chunk_size)

    file.close()


##########################################################################
# Load
##########################################################################


def load(context):
    data_context = DataContext()

    load_file(context, data_context)

    hierarchy = data_context.hierarchy
    hlod = data_context.hlod
    animation = data_context.animation
    compressed_animation = data_context.compressed_animation

    if hierarchy is None:
        sklpath = None

        if hlod and hlod.header.model_name != hlod.header.hierarchy_name:
            sklpath = os.path.dirname(context.filepath) + os.path.sep + \
                hlod.header.hierarchy_name.lower() + '.w3d'

        # if we load a animation file afterwards and need the hierarchy again
        elif animation and animation.header.name != '':
            sklpath = os.path.dirname(context.filepath) + os.path.sep + \
                animation.header.hierarchy_name.lower() + '.w3d'
        elif compressed_animation and compressed_animation.header.name != '':
            sklpath = os.path.dirname(context.filepath) + os.path.sep + \
                compressed_animation.header.hierarchy_name.lower() + '.w3d'

        if sklpath:
            load_file(context, data_context, sklpath)
            if data_context.hierarchy is None:
                context.error(
                    f'hierarchy file not found: {sklpath}. Make sure it is right next to the file you are importing.')
                return

    create_data(context,
                data_context.meshes,
                data_context.hlod,
                data_context.hierarchy,
                data_context.collision_boxes,
                data_context.animation,
                data_context.compressed_animation,
                data_context.dazzles)
    return {'FINISHED'}


##########################################################################
# Unsupported
##########################################################################

W3D_CHUNK_MORPH_ANIMATION = 0x000002C0
W3D_CHUNK_HMODEL = 0x00000300
W3D_CHUNK_LODMODEL = 0x00000400
W3D_CHUNK_COLLECTION = 0x00000420
W3D_CHUNK_POINTS = 0x00000440
W3D_CHUNK_LIGHT = 0x00000460
W3D_CHUNK_EMITTER = 0x00000500
W3D_CHUNK_AGGREGATE = 0x00000600
W3D_CHUNK_NULL_OBJECT = 0x00000750
W3D_CHUNK_LIGHTSCAPE = 0x00000800
W3D_CHUNK_SOUNDROBJ = 0x00000A00
