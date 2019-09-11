# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import struct
from mathutils import Vector, Quaternion

STRING_LENGTH = 16
LARGE_STRING_LENGTH = 32


def read_string(io_stream):
    str_buf = []
    byte = io_stream.read(1)
    while ord(byte) != 0:
        str_buf.append(byte)
        byte = io_stream.read(1)
    return (b"".join(str_buf)).decode("utf-8")


def write_string(io_stream, string):
    io_stream.write(bytes(string, 'UTF-8'))
    io_stream.write(struct.pack('B', 0b0))


def read_fixed_string(io_stream):
    return ((str(io_stream.read(STRING_LENGTH)))[2:18]).split("\\")[0]


def write_fixed_string(io_stream, string):
    # truncate the string to 16
    nullbytes = STRING_LENGTH - len(string)
    if nullbytes < 0:
        print("Warning: Fixed string is too long!")

    io_stream.write(bytes(string, 'UTF-8')[0:STRING_LENGTH])
    i = 0
    while i < nullbytes:
        io_stream.write(struct.pack("B", 0b0))
        i += 1


def read_long_fixed_string(io_stream):
    return ((str(io_stream.read(LARGE_STRING_LENGTH)))[2:34]).split("\\")[0]


def write_long_fixed_string(io_stream, string):
    # truncate the string to 32
    nullbytes = LARGE_STRING_LENGTH - len(string)
    if nullbytes < 0:
        print("Warning: Fixed string was too long!")

    io_stream.write(bytes(string, 'UTF-8')[0:LARGE_STRING_LENGTH])
    i = 0
    while i < nullbytes:
        io_stream.write(struct.pack("B", 0b0))
        i += 1


def read_long(io_stream):
    return struct.unpack("<l", io_stream.read(4))[0]


def write_long(io_stream, num):
    io_stream.write(struct.pack("<l", num))


def read_ulong(io_stream):
    return struct.unpack("<L", io_stream.read(4))[0]


def write_ulong(io_stream, num):
    io_stream.write(struct.pack("<L", num))


def read_short(io_stream):
    return struct.unpack("<h", io_stream.read(2))[0]


def write_short(io_stream, num):
    io_stream.write(struct.pack("<h", num))


def read_ushort(io_stream):
    return struct.unpack("<H", io_stream.read(2))[0]


def write_ushort(io_stream, num):
    io_stream.write(struct.pack("<H", num))


def read_float(io_stream):
    return struct.unpack("<f", io_stream.read(4))[0]


def write_float(io_stream, num):
    io_stream.write(struct.pack("<f", num))


def read_byte(io_stream):
    return struct.unpack("<b", io_stream.read(1))[0]


def read_ubyte(io_stream):
    return struct.unpack("<B", io_stream.read(1))[0]


def write_ubyte(io_stream, byte):
    io_stream.write(struct.pack("<B", byte))


def read_vector(io_stream):
    return Vector((read_float(io_stream), read_float(io_stream), read_float(io_stream)))


def write_vector(io_stream, vec):
    write_float(io_stream, vec[0])
    write_float(io_stream, vec[1])
    write_float(io_stream, vec[2])


def read_quaternion(io_stream):
    quat = (read_float(io_stream), read_float(io_stream),
            read_float(io_stream), read_float(io_stream))
    # change order from xyzw to wxyz
    return Quaternion((quat[3], quat[0], quat[1], quat[2]))


def write_quaternion(io_stream, quat):
    # changes the order from wxyz to xyzw
    write_float(io_stream, quat[1])
    write_float(io_stream, quat[2])
    write_float(io_stream, quat[3])
    write_float(io_stream, quat[0])


def read_vector2(io_stream):
    return (read_float(io_stream), read_float(io_stream))


def write_vector2(io_stream, vec):
    write_float(io_stream, vec[0])
    write_float(io_stream, vec[1])


def write_long_array(io_stream, array):
    for val in array:
        write_long(io_stream, val)


def read_channel_value(io_stream, channel_type):
    if channel_type == 6:
        return read_quaternion(io_stream)
    return read_float(io_stream)


def read_chunk_head(io_stream):
    chunk_type = read_ulong(io_stream)
    chunk_size = read_ulong(io_stream) & 0x7FFFFFFF
    chunk_end = io_stream.tell() + chunk_size
    return (chunk_type, chunk_size, chunk_end)


def write_chunk_head(io_stream, chunk_id, size, has_sub_chunks=False):
    write_ulong(io_stream, chunk_id)
    if has_sub_chunks:
        size |= 0x80000000
    write_ulong(io_stream, size)


def write_array(io_stream, data, write_func):
    for dat in data:
        write_func(io_stream, dat)
