# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

from .common.utils.mesh_import import *
from .common.utils.hierarchy_import import *
from .common.utils.material_import import deduplicate_materials
from .common.utils.animation_import import *
from .common.utils.box_import import *
from .w3d.utils.dazzle_import import *


def create_data(context, meshes, hlod=None, hierarchy=None, boxes=None, animation=None, compressed_animation=None,
                dazzles=None):
    boxes = boxes if boxes is not None else []
    dazzles = dazzles if dazzles is not None else []
    collection = get_collection(hlod)

    # every mesh gets its own materials during creation below, even when several
    # meshes reference an identical definition; merge those once everything is built
    materials_before = set(bpy.data.materials)

    mesh_names_map = {}
    if hlod is not None:
        current_coll = collection
        for i, lod_array in enumerate(reversed(hlod.lod_arrays)):
            if i > 0:
                current_coll = get_collection(hlod, '.' + str(i))
                current_coll.hide_viewport = True

            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        newname = create_mesh(context, mesh, current_coll)
                        mesh_names_map[mesh.name()] = newname

                for box in boxes:
                    if box.name() == sub_object.name:
                        create_box(box, collection)

                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        create_dazzle(context, dazzle, collection)

    rig = get_or_create_skeleton(hierarchy, collection)

    if hlod is not None:
        for lod_array in reversed(hlod.lod_arrays):
            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        mesh.header.mesh_name = mesh_names_map[mesh.name()]
                        rig_mesh(mesh, hierarchy, rig, sub_object)
                for box in boxes:
                    if box.name() == sub_object.name:
                        rig_box(box, hierarchy, rig, sub_object)
                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        dazzle_object = bpy.data.objects[dazzle.name()]
                        rig_object(dazzle_object, hierarchy, rig, sub_object)

    else:
        for mesh in meshes:
            create_mesh(context, mesh, collection)

    create_animation(context, rig, animation, hierarchy)
    create_animation(context, rig, compressed_animation, hierarchy)

    merged = deduplicate_materials(set(bpy.data.materials) - materials_before)
    if merged:
        context.info(f'merged {merged} duplicate material(s)')
