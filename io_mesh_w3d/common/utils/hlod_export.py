# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.structs.hlod import *


screen_sizes = [MAX_SCREEN_SIZE, 1.0, 0.3, 0.03]


def create_lod_array(meshes, hierarchy, container_name, lod_arrays):
    if not meshes:
        return lod_arrays

    index = min(len(lod_arrays), len(screen_sizes) - 1)

    lod_array = HLodLodArray(
        header=HLodArrayHeader(
            model_count=len(meshes),
            max_screen_size=screen_sizes[index]),
        sub_objects=[])

    for mesh in meshes:
        sub_object = HLodSubObject(
            name=mesh.name,
            identifier=container_name + '.' + mesh.name,
            bone_index=0,
            is_box=mesh.data.object_type == 'BOX')

        if not mesh.vertex_groups:
            for index, pivot in enumerate(hierarchy.pivots):
                if pivot.name == mesh.parent_bone or pivot.name == mesh.name:
                    sub_object.bone_index = index

        lod_array.sub_objects.append(sub_object)

    lod_arrays.append(lod_array)
    return lod_arrays


def create_hlod(hierarchy, container_name):
    hlod = HLod(
        header=HLodHeader(
            model_name=container_name,
            hierarchy_name=hierarchy.name()),
        lod_arrays=[])

    meshes = get_objects('MESH', bpy.context.scene.collection.objects)
    lod_arrays = create_lod_array(meshes, hierarchy, container_name, [])

    for coll in bpy.data.collections:
        meshes = get_objects('MESH', coll.objects)
        lod_arrays = create_lod_array(
            meshes, hierarchy, container_name, lod_arrays)

    for lod_array in reversed(lod_arrays):
        hlod.lod_arrays.append(lod_array)
    hlod.header.lod_count = len(hlod.lod_arrays)
    return hlod
