# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.shared.structs.collision_box import *
from io_mesh_w3d.shared.structs.data_context import *
from io_mesh_w3d.shared.structs.hierarchy import *
from io_mesh_w3d.shared.structs.hlod import *
from io_mesh_w3d.shared.structs.mesh import *
from io_mesh_w3d.w3d.structs.dazzle import *
from io_mesh_w3d.w3d.structs.compressed_animation import *


def load_file(context, path, data_context):
    path = insensitive_path(path)
    print('Loading file', path)

    if not os.path.exists(path):
        context.error('file not found: ' + path)
        return data_context

    file = open(path, "rb")
    filesize = os.path.getsize(path)

    while file.tell() < filesize:
        (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

        if chunk_type == W3D_CHUNK_MESH:
            data_context.meshes.append(Mesh.read(context, file, chunk_end))
        elif chunk_type == W3D_CHUNK_HIERARCHY:
            data_context.hierarchy = Hierarchy.read(context, file, chunk_end)
        elif chunk_type == W3D_CHUNK_ANIMATION:
            data_context.animation = Animation.read(context, file, chunk_end)
        elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION:
            data_context.compressed_animation = CompressedAnimation.read(
                context, file, chunk_end)
        elif chunk_type == W3D_CHUNK_HLOD:
            data_context.hlod = HLod.read(context, file, chunk_end)
        elif chunk_type == W3D_CHUNK_BOX:
            data_context.collision_boxes.append(CollisionBox.read(file))
        elif chunk_type == W3D_CHUNK_DAZZLE:
            data_context.dazzles.append(Dazzle.read(context, file, chunk_end))
        elif chunk_type == W3D_CHUNK_MORPH_ANIMATION:
            print("-> morph animation chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_HMODEL:
            print("-> hmodel chnuk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LODMODEL:
            print("-> lodmodel chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_COLLECTION:
            print("-> collection chunk not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_POINTS:
            print("-> points chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LIGHT:
            print("-> light chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_EMITTER:
            print("-> emitter chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_AGGREGATE:
            print("-> aggregate chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_NULL_OBJECT:
            print("-> null object chunkt is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LIGHTSCAPE:
            print("-> lightscape chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_SOUNDROBJ:
            print("-> soundobj chunk is not supported")
            file.seek(chunk_size, 1)
        else:
            skip_unknown_chunk(context, file, chunk_type, chunk_size)

    file.close()

    return data_context


##########################################################################
# Load
##########################################################################


def load(context, import_settings):
    data_context = DataContext(
        meshes=[],
        dazzles=[],
        textures=[],
        collision_boxes=[],
        hierarchy=None,
        hlod=None,
        animation=None,
        compressed_animation=None)

    data_context = load_file(context, context.filepath, data_context)

    hierarchy = data_context.hierarchy
    hlod = data_context.hlod
    animation = data_context.animation
    compressed_animation = data_context.compressed_animation

    if hierarchy is None:
        sklpath = None
        if hlod is not None and hlod.header.model_name != hlod.header.hierarchy_name:
            sklpath = os.path.dirname(context.filepath) + "/" + \
                hlod.header.hierarchy_name.lower() + ".w3d"

        # if we load a animation file afterwards and need the hierarchy again
        elif animation is not None and animation.header.name != "":
            sklpath = os.path.dirname(context.filepath) + "/" + \
                animation.header.hierarchy_name.lower() + ".w3d"
        elif compressed_animation is not None and compressed_animation.header.name != "":
            sklpath = os.path.dirname(context.filepath) + "/" + \
                compressed_animation.header.hierarchy_name.lower() + ".w3d"

        if sklpath is not None:
            data_context = load_file(context, sklpath, data_context)
            if data_context.hierarchy is None:
                context.error('hierarchy file not found: ' + sklpath)

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
