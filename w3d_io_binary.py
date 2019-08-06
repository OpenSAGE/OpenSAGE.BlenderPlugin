#Written by Stephan Vedder and Michael Schnabel
#Last Modification 05.08.2019
import bpy
import struct
from mathutils import Vector, Quaternion
from io_mesh_w3d.w3d_structs import *

def get_chunk_size(data):
    return (data & 0x7FFFFFFF)
    
def make_chunk_size(data):
    return (data | 0x80000000)

def get_version(data):
    return Version(major = (data)>>16, minor = (data) & 0xFFFF)
    
def make_version(version):
    return (((version.major) << 16) | (version.minor))

def read_string(file):
    bytes = []
    b = file.read(1)
    while ord(b) != 0:
        bytes.append(b)
        b = file.read(1)
    return (b"".join(bytes)).decode("utf-8")
    
def write_string(file, string):
    file.write(bytes(string, 'UTF-8'))
    #write binary 0
    file.write(struct.pack('B', 0))
   
def read_fixed_string(file):
    return ((str(file.read(16)))[2:18]).split("\\")[0]
    
def write_fixed_string(file, string):
    #truncate the string to 16
    nullbytes = 16-len(string)
    if(nullbytes<0):
        print("Warning: Fixed string is too long")

    file.write(bytes(string, 'UTF-8'))
    for i in range(nullbytes):
        file.write(struct.pack("B", 0))

def read_long_fixed_string(file):
    return ((str(file.read(32)))[2:34]).split("\\")[0]
    
def write_long_fixed_string(file, string):
    #truncate the string to 32
    nullbytes = 32-len(string)
    if(nullbytes<0):
        print("Warning: Fixed string is too long")

    file.write(bytes(string, 'UTF-8'))
    for i in range(nullbytes):
        file.write(struct.pack("B", 0))
 
def read_rgba(file):
    return RGBA(r=ord(file.read(1)), g=ord(file.read(1)), b=ord(file.read(1)), a=ord(file.read(1)))
    
def write_rgba(file, rgba):
    file.write(struct.pack("B", rgba.r))
    file.write(struct.pack("B", rgba.g))
    file.write(struct.pack("B", rgba.b))
    file.write(struct.pack("B", rgba.a))   
 
def read_long(file):
    return struct.unpack("<L", file.read(4))[0]
    
def write_long(file, num):
    file.write(struct.pack("<L", num))

def read_short(file):
    return struct.unpack("<H", file.read(2))[0]
    
def write_short(file, num):
    file.write(struct.pack("<H", num))

def read_float(file):
    return struct.unpack("<f", file.read(4))[0]

def write_float(file, num):
	file.write(struct.pack("<f", num))

def read_long_array(file, chunkEnd):
    longArray = []
    while file.tell() < chunkEnd:
        longArray.append(read_long(file))
    return longArray
    
def write_long_array(file, array):
    for a in array:
        write_long(file, a)
        
def read_unsigned_byte(file):
    return struct.unpack("<B", file.read(1))[0]

def WriteUnsignedByte(file, byte):
    file.write(struct.pack("<B", byte))
    
def read_vector(file):
    return Vector((read_float(file), read_float(file), read_float(file)))
    
def write_vector(file, vec):
    write_float(file, vec[0])
    write_float(file, vec[1])
    write_float(file, vec[2])

def read_quaternion(file):
    quat = (read_float(file), read_float(file), read_float(file), read_float(file))
    #change order from xyzw to wxyz
    return Quaternion((quat[3], quat[0], quat[1], quat[2]))
    
def write_quaternion(file, quat):
    #changes the order from wxyz to xyzw
    write_float(file, quat[1])
    write_float(file, quat[2])
    write_float(file, quat[3])
    write_float(file, quat[0])

def read_mesh_vertices_array(file, chunkEnd):
    verts = []
    while file.tell() < chunkEnd:
        verts.append(read_vector(file))
    return verts
