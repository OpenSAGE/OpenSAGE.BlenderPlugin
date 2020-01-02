# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.w3d.structs.mesh import *
from io_mesh_w3d.w3d.structs.hierarchy import *
from io_mesh_w3d.w3d.structs.animation import *
from io_mesh_w3d.w3d.structs.compressed_animation import *
from io_mesh_w3d.w3d.structs.box import *
from io_mesh_w3d.w3d.structs.hlod import *

from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.import_utils import *


##########################################################################
# hierarchy
##########################################################################


def load_hierarchy_file(self, sklpath):
    hierarchy = None
    path = insensitive_path(sklpath)
    file = open(path, "rb")
    filesize = os.path.getsize(path)

    while file.tell() < filesize:
        (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

        if chunk_type == W3D_CHUNK_HIERARCHY:
            hierarchy = Hierarchy.read(self, file, chunk_end)
        else:
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

    file.close()

    return hierarchy

##########################################################################
# Load
##########################################################################


def load(self, import_settings):
    print('Loading file', self.filepath)

    file = open(self.filepath, "rb")
    filesize = os.path.getsize(self.filepath)

    mesh_structs = []
    hierarchy = None
    animation = None
    compressedAnimation = None
    hlod = None
    box = None

    while file.tell() < filesize:
        (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

        if chunk_type == W3D_CHUNK_MESH:
            mesh_structs.append(Mesh.read(self, file, chunk_end))
        elif chunk_type == W3D_CHUNK_HIERARCHY:
            hierarchy = Hierarchy.read(self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_ANIMATION:
            animation = Animation.read(self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION:
            compressedAnimation = CompressedAnimation.read(
                self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_HLOD:
            hlod = HLod.read(self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_BOX:
            box = Box.read(file)
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
        elif chunk_type == W3D_CHUNK_DAZZLE:
            print("-> dazzle chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_SOUNDROBJ:
            print("-> soundobj chunk is not supported")
            file.seek(chunk_size, 1)
        else:
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

    file.close()

    if hierarchy is None:
        sklpath = None
        if hlod is not None and hlod.header.model_name != hlod.header.hierarchy_name:
            sklpath = os.path.dirname(self.filepath) + "/" + \
                hlod.header.hierarchy_name.lower() + ".w3d"

        # if we load a animation file afterwards and need the hierarchy again
        elif animation is not None and animation.header.name != "":
            sklpath = os.path.dirname(self.filepath) + "/" + \
                animation.header.hierarchy_name.lower() + ".w3d"
        elif compressedAnimation is not None and compressedAnimation.header.name != "":
            sklpath = os.path.dirname(self.filepath) + "/" + \
                compressedAnimation.header.hierarchy_name.lower() + ".w3d"

        if sklpath is not None:
            try:
                hierarchy = load_hierarchy_file(self, sklpath)
            except FileNotFoundError:
                print("!!! hierarchy file not found: " + sklpath)
                self.report({'ERROR'}, "hierarchy file not found: " + sklpath)

    coll = get_collection(hlod)

    meshes = []
    for mesh_struct in mesh_structs:
        meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

    rig = get_or_create_skeleton(hlod, hierarchy, coll)
    create_box(box, hlod, hierarchy, rig, coll)

    # need an extra loop because the order of the meshes is random
    for i, mesh_struct in enumerate(mesh_structs):
        rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

    create_animation(rig, animation, hierarchy)
    create_animation(rig, compressedAnimation, hierarchy, compressed=True)

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
W3D_CHUNK_DAZZLE = 0x00000900
W3D_CHUNK_SOUNDROBJ = 0x00000A00
