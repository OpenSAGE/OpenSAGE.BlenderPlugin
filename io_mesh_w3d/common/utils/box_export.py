# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.structs.collision_box import *


def retrieve_boxes(context, container_name):
    boxes = []

    for mesh_object in get_objects('MESH'):
        if mesh_object.data.object_type != 'BOX':
            continue
        name = container_name + '.' + mesh_object.name

        if Vector(mesh_object.rotation_euler) != Vector((0,0,0)):
            context.warning(f'Rotation on the collision box is not supported. Resetting to 0!')
            mesh_object.rotation_euler = (0,0,0)

        center = get_aa_center(mesh_object.data.vertices, mesh_object.matrix_local)
        extend = get_aa_box(mesh_object.data.vertices, mesh_object.matrix_local)

        box = CollisionBox(
            name_=name,
            center=center,
            extend=extend)

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
