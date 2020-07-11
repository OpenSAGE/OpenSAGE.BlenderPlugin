# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import struct

from mathutils import Vector, Quaternion

HEAD = 8  # chunk_type(long) + chunk_size(long)
STRING_LENGTH = 16
LARGE_STRING_LENGTH = STRING_LENGTH * 2


def read_string(io_stream):
    str_buf = []
    byte = io_stream.read(1)
    while ord(byte) != 0:
        str_buf.append(byte)
        byte = io_stream.read(1)
    return (b''.join(str_buf)).decode('utf-8')


def write_string(string, io_stream):
    io_stream.write(bytes(string, 'UTF-8'))
    io_stream.write(struct.pack('B', 0b0))


def read_fixed_string(io_stream):
    return ((str(io_stream.read(STRING_LENGTH)))[2:18]).split('\\')[0]


def write_fixed_string(string, io_stream):
    # truncate the string to 16
    nullbytes = STRING_LENGTH - len(string)
    if nullbytes < 0:
        print('Warning: Fixed string is too long!')

    io_stream.write(bytes(string, 'UTF-8')[0:STRING_LENGTH])
    i = 0
    while i < nullbytes:
        io_stream.write(struct.pack('B', 0b0))
        i += 1


def read_long_fixed_string(io_stream):
    return ((str(io_stream.read(LARGE_STRING_LENGTH)))[2:34]).split('\\')[0]


def write_long_fixed_string(string, io_stream):
    # truncate the string to 32
    nullbytes = LARGE_STRING_LENGTH - len(string)
    if nullbytes < 0:
        print('Warning: Fixed string was too long!')

    io_stream.write(bytes(string, 'UTF-8')[0:LARGE_STRING_LENGTH])
    i = 0
    while i < nullbytes:
        io_stream.write(struct.pack('B', 0b0))
        i += 1


def read_long(io_stream):
    return struct.unpack('<l', io_stream.read(4))[0]


def write_long(num, io_stream):
    io_stream.write(struct.pack('<l', num))


def read_ulong(io_stream):
    return struct.unpack('<L', io_stream.read(4))[0]


def write_ulong(num, io_stream):
    io_stream.write(struct.pack('<L', num))


def read_short(io_stream):
    return struct.unpack('<h', io_stream.read(2))[0]


def write_short(num, io_stream):
    io_stream.write(struct.pack('<h', num))


def read_ushort(io_stream):
    return struct.unpack('<H', io_stream.read(2))[0]


def write_ushort(num, io_stream):
    io_stream.write(struct.pack('<H', num))


def read_float(io_stream):
    return struct.unpack('<f', io_stream.read(4))[0]


def write_float(num, io_stream):
    io_stream.write(struct.pack('<f', num))


def read_byte(io_stream):
    return struct.unpack('<b', io_stream.read(1))[0]


def write_byte(byte, io_stream):
    io_stream.write(struct.pack('<b', byte))


def read_ubyte(io_stream):
    return struct.unpack('<B', io_stream.read(1))[0]


def write_ubyte(byte, io_stream):
    io_stream.write(struct.pack('<B', byte))


def read_vector(io_stream):
    vec = Vector((0, 0, 0))
    vec.x = read_float(io_stream)
    vec.y = read_float(io_stream)
    vec.z = read_float(io_stream)
    return vec


def write_vector(vec, io_stream):
    write_float(vec.x, io_stream)
    write_float(vec.y, io_stream)
    write_float(vec.z, io_stream)


def read_vector4(io_stream):
    vec = Vector((0, 0, 0, 0))
    vec.x = read_float(io_stream)
    vec.y = read_float(io_stream)
    vec.z = read_float(io_stream)
    vec.w = read_float(io_stream)
    return vec


def write_vector4(vec, io_stream):
    write_float(vec.x, io_stream)
    write_float(vec.y, io_stream)
    write_float(vec.z, io_stream)
    write_float(vec.w, io_stream)


def read_quaternion(io_stream):
    quat = Quaternion((0, 0, 0, 0))
    quat.x = read_float(io_stream)
    quat.y = read_float(io_stream)
    quat.z = read_float(io_stream)
    quat.w = read_float(io_stream)
    return quat


def write_quaternion(quat, io_stream):
    write_float(quat.x, io_stream)
    write_float(quat.y, io_stream)
    write_float(quat.z, io_stream)
    write_float(quat.w, io_stream)


def read_vector2(io_stream):
    vec = Vector((0, 0, 0))
    vec.x = read_float(io_stream)
    vec.y = read_float(io_stream)
    return vec


def write_vector2(vec, io_stream):
    write_float(vec.x, io_stream)
    write_float(vec.y, io_stream)


def read_channel_value(io_stream, channel_type):
    if channel_type == 6:
        return read_quaternion(io_stream)
    return read_float(io_stream)


def write_channel_value(data, io_stream, channel_type):
    if channel_type == 6:
        write_quaternion(data, io_stream)
    else:
        write_float(data, io_stream)


def read_chunk_head(io_stream):
    chunk_type = read_ulong(io_stream)
    chunk_size = read_ulong(io_stream) & 0x7FFFFFFF
    chunk_end = io_stream.tell() + chunk_size
    return chunk_type, chunk_size, chunk_end


def write_chunk_head(chunk_id, io_stream, size, has_sub_chunks=False):
    write_ulong(chunk_id, io_stream)
    if has_sub_chunks:
        size |= 0x80000000
    write_ulong(size, io_stream)


def write_list(data, io_stream, write_func, par1=None):
    for datum in data:
        if par1 is not None:
            write_func(datum, io_stream, par1)
        else:
            write_func(datum, io_stream)


def read_list(io_stream, chunk_end, read_func):
    result = []
    while io_stream.tell() < chunk_end:
        result.append(read_func(io_stream))
    return result


def read_fixed_list(io_stream, count, read_func, par1=None):
    result = []
    for _ in range(count):
        if par1 is not None:
            result.append(read_func(io_stream, par1))
        else:
            result.append(read_func(io_stream))
    return result
