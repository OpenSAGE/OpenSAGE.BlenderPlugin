# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.shared.utils.import_basics import *


def create_box(box, hlod, hierarchy, rig, coll):
    if box is None:
        return

    x = box.extend[0] / 2.0
    y = box.extend[1] / 2.0
    z = box.extend[2]

    verts = [(x, y, z), (-x, y, z), (-x, -y, z), (x, -y, z),
             (x, y, 0), (-x, y, 0), (-x, -y, 0), (x, -y, 0)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]

    cube = bpy.data.meshes.new(box.name())
    cube.from_pydata(verts, [], faces)
    cube.update(calc_edges=True)
    box_object = bpy.data.objects.new(box.name(), cube)
    box_object.object_type = 'BOX'
    box_object.display_type = 'WIRE'
    mat = bpy.data.materials.new(box.name() + ".Material")

    mat.diffuse_color = box.color.to_vector_rgba()
    cube.materials.append(mat)
    box_object.location = box.center
    link_object_to_active_scene(box_object, coll)

    if hierarchy is None or rig is None:
        return

    sub_objects = [
        sub_object for sub_object in hlod.lod_arrays[-1].sub_objects if sub_object.name == box.name()]
    if not sub_objects:
        return
    sub_object = sub_objects[0]
    if sub_object.bone_index == 0:
        return
    pivot = hierarchy.pivots[sub_object.bone_index]
    box_object.parent = rig
    box_object.parent_bone = pivot.name
    box_object.parent_type = 'BONE'
