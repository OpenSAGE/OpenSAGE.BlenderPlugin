# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.shared.utils.basics import *
from io_mesh_w3d.w3d.structs.dazzle import *


def retrieve_dazzles(hierarchy, container_name):
    dazzles = []

    for mesh_object in get_objects('MESH'):
        if mesh_object.object_type != 'DAZZLE':
            continue
        name = container_name + '.' + mesh_object.name
        dazzle = Dazzle(
            name_=name,
            type_name=mesh_object.dazzle_type)

        dazzles.append(dazzle)
    return dazzles