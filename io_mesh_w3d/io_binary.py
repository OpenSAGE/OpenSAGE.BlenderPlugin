# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
import struct
from mathutils import Vector, Quaternion

STRING_LENGTH = 16
LARGE_STRING_LENGTH = 32


def read_string(file):
    bytes = []
    b = file.read(1)
    while ord(b) != 0:
        bytes.append(b)
        b = file.read(1)
    return (b"".join(bytes)).decode("utf-8")


def write_string(file, string):
    file.write(bytes(string, 'UTF-8'))
    file.write(struct.pack('B', 0b0))


def read_fixed_string(file):
    return ((str(file.read(STRING_LENGTH)))[2:18]).split("\\")[0]


def write_fixed_string(file, string):
    # truncate the string to 16
    nullbytes = STRING_LENGTH - len(string)
    if nullbytes < 0:
        print("Warning: Fixed string is too long!")

    file.write(bytes(string, 'UTF-8')[0:STRING_LENGTH])
    i = 0
    while i < nullbytes:
        file.write(struct.pack("B", 0b0))
        i += 1


def read_long_fixed_string(file):
    return ((str(file.read(LARGE_STRING_LENGTH)))[2:34]).split("\\")[0]


def write_long_fixed_string(file, string):
    # truncate the string to 32
    nullbytes = LARGE_STRING_LENGTH - len(string)
    if nullbytes < 0:
        print("Warning: Fixed string was too long!")

    file.write(bytes(string, 'UTF-8')[0:LARGE_STRING_LENGTH])
    i = 0
    while i < nullbytes:
        file.write(struct.pack("B", 0b0))
        i += 1


def read_long(file):
    return struct.unpack("<l", file.read(4))[0]


def write_long(file, num):
    file.write(struct.pack("<l", num))


def read_ulong(file):
    return struct.unpack("<L", file.read(4))[0]


def write_ulong(file, num):
    file.write(struct.pack("<L", num))


def read_ushort(file):
    return struct.unpack("<H", file.read(2))[0]


def write_ushort(file, num):
    file.write(struct.pack("<H", num))


def read_short(file):
    return struct.unpack("<h", file.read(2))[0]


def write_short(file, num):
    file.write(struct.pack("<h", num))


def read_float(file):
    return struct.unpack("<f", file.read(4))[0]


def write_float(file, num):
    file.write(struct.pack("<f", num))


def write_long_array(file, array):
    for a in array:
        write_long(file, a)


def read_byte(file):
    return struct.unpack("<b", file.read(1))[0]


def read_ubyte(file):
    return struct.unpack("<B", file.read(1))[0]


def write_ubyte(file, byte):
    file.write(struct.pack("<B", byte))


def read_vector(file):
    return Vector((read_float(file), read_float(file), read_float(file)))


def write_vector(file, vec):
    write_float(file, vec[0])
    write_float(file, vec[1])
    write_float(file, vec[2])


def read_quaternion(file):
    quat = (read_float(file), read_float(file),
            read_float(file), read_float(file))
    # change order from xyzw to wxyz
    return Quaternion((quat[3], quat[0], quat[1], quat[2]))


def write_quaternion(file, quat):
    # changes the order from wxyz to xyzw
    write_float(file, quat[1])
    write_float(file, quat[2])
    write_float(file, quat[3])
    write_float(file, quat[0])


def read_channel_value(file, type):
    if type == 6:
        return read_quaternion(file)
    else:
        return read_float(file)


def read_vector2(file):
    return (read_float(file), read_float(file))


def write_vector2(file, vec):
    write_float(file, vec[0])
    write_float(file, vec[1])
