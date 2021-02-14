# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import sys

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

        box.extend = get_aa_box(mesh_object.data.vertices)

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

        for material in mesh_object.data.materials:
            box.color = RGBA(material.diffuse_color)
        boxes.append(box)
    return boxes


def get_aa_box(vertices):
    minX = sys.float_info.max
    maxX = sys.float_info.min

    minY = sys.float_info.max
    maxY = sys.float_info.min

    minZ = sys.float_info.max
    maxZ = sys.float_info.min

    for vertex in vertices:
        minX = min(vertex.co.x, minX)
        maxX = max(vertex.co.x, maxX)

        minY = min(vertex.co.y, minY)
        maxY = max(vertex.co.y, maxY)

        minZ = min(vertex.co.z, minZ)
        maxZ = max(vertex.co.z, maxZ)

    return Vector((maxX - minX, maxY - minY, maxZ - minZ))
