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
        box.extend = Vector(
            (box_mesh.vertices[0].co.x * 2,
             box_mesh.vertices[0].co.y * 2,
             box_mesh.vertices[0].co.z))

        for material in box_mesh.materials:
            box.color = RGBA(material.diffuse_color)
        boxes.append(box)
    return boxes
