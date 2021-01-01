# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.structs.collision_box import *


def retrieve_boxes(container_name):
    boxes = []

    for mesh_object in get_objects('MESH'):
        if mesh_object.data.object_type != 'BOX':
            continue
        name = container_name + '.' + mesh_object.name
        box = CollisionBox(
            name_=name,
            center=mesh_object.location)
        box_mesh = mesh_object.to_mesh(preserve_all_data_layers=False, depsgraph=None)
        # TODO: use mesh_object.bound_box ? 
        box.extend = Vector(
            (box_mesh.vertices[0].co.x * 2,
             box_mesh.vertices[0].co.y * 2,
             box_mesh.vertices[0].co.z))

        box.box_type = int(mesh_object.data.box_type)

        if 'PHYSICAL' in mesh_object.data.box_collision_types:
            box.collision_types |= COLLISION_TYPE_PHYSICAL
        if 'PROJECTILE' in mesh_object.data.box_collision_types:
            box.collision_types |= COLLISION_TYPE_PROJECTILE
        if 'VIS' in mesh_object.data.box_collision_types:
            box.collision_types |= COLLISION_TYPE_VIS
        if 'CAMERA' in mesh_object.data.box_collision_types:
            box.collision_types |= COLLISION_TYPE_CAMERA
        if 'VEHICLE' in mesh_object.data.box_collision_types:
            box.collision_types |= COLLISION_TYPE_VEHICLE

        for material in box_mesh.materials:
            box.color = RGBA(material.diffuse_color)
        boxes.append(box)
    return boxes
