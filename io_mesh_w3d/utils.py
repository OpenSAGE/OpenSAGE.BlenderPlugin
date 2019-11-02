# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs.struct import HEAD


def const_size(size, include_head=True):
    if include_head:
        size += HEAD
    return size


def text_size(text, include_head=True):
    if not len(text):
        return 0
    size = len(text) + 1
    if include_head:
        size += HEAD
    return size


def list_size(objects, include_head=True):
    if not objects:
        return 0
    size = 0
    if include_head:
        size += HEAD
    for obj in objects:
        size += obj.size()
    return size


def vec_list_size(list, include_head=True):
    return data_list_size(list, include_head, 12)


def vec2_list_size(list, include_head=True):
    return data_list_size(list, include_head, 8)


def long_list_size(list, include_head=True):
    return data_list_size(list, include_head, 4)


def data_list_size(list, include_head=True, data_size=1):
    if not list:
        return 0
    size = len(list) * data_size
    if include_head:
        size += HEAD
    return size


def write_object_list(io_stream, objects, write_func):
    for obj in objects:
        write_func(obj, io_stream)
