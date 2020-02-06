# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bmesh
import bpy

from io_mesh_w3d.common.utils.mesh_import import *
from io_mesh_w3d.common.utils.hierarchy_import import *
from io_mesh_w3d.common.utils.animation_import import *
from io_mesh_w3d.common.utils.material_import import *
from io_mesh_w3d.common.utils.box_import import *
from io_mesh_w3d.common.utils.primitives import *
from io_mesh_w3d.w3d.utils.dazzle_import import *


def create_data(
        context,
        meshes,
        hlod=None,
        hierarchy=None,
        boxes=[],
        animation=None,
        compressed_animation=None,
        dazzles=[]):
    rig = None
    coll = get_collection(hlod)

    rig = get_or_create_skeleton(hlod, hierarchy, coll)

    if hlod is not None:
        current_coll = coll
        for i, lod_array in enumerate(reversed(hlod.lod_arrays)):
            if i > 0:
                current_coll = get_collection(hlod, '.' + str(i))
                # collection has no hide_set()
                current_coll.hide_viewport = True

            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        create_mesh(context, mesh, hierarchy, current_coll)

                for box in boxes:
                    if box.name() == sub_object.name:
                        create_box(box, hlod, hierarchy, rig, coll)

                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        create_dazzle(context, dazzle, hlod, hierarchy, rig, coll)

        for lod_array in reversed(hlod.lod_arrays):
            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        rig_mesh(mesh, hierarchy, rig, sub_object)
                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        dazzle_object = bpy.data.objects[dazzle.name()]
                        rig_object(dazzle_object, hierarchy, rig, sub_object)

    else:
        for mesh in meshes:
            create_mesh(context, mesh, hierarchy, coll)

    create_animation(context, rig, animation, hierarchy)
    create_animation(context, rig, compressed_animation, hierarchy, compressed=True)