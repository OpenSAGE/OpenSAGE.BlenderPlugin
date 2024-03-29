# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.io_binary import *


def skip_unknown_chunk(context, io_stream, chunk_type, chunk_size):
    context.warning(f'unknown chunk_type in io_stream: {hex(chunk_type)}')
    io_stream.seek(chunk_size, 1)


def read_chunk_array(context, io_stream, chunk_end, type_, read_func):
    result = []

    while io_stream.tell() < chunk_end:
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        if chunk_type == type_:
            result.append(read_func(context, io_stream, subchunk_end))
        else:
            skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
    return result


def const_size(size, include_head=True):
    if include_head:
        size += HEAD
    return size


def text_size(text, include_head=True):
    if len(text) == 0:
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


def vec_list_size(vec_list, include_head=True):
    return data_list_size(vec_list, include_head, 12)


def vec2_list_size(vec_list, include_head=True):
    return data_list_size(vec_list, include_head, 8)


def long_list_size(vec_list, include_head=True):
    return data_list_size(vec_list, include_head, 4)


def data_list_size(data_list, include_head=True, data_size=1):
    if not data_list:
        return 0
    size = len(data_list) * data_size
    if include_head:
        size += HEAD
    return size
