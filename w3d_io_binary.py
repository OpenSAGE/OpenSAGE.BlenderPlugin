#Written by Stephan Vedder and Michael Schnabel
#Last Modification 05.08.2019

def GetChunkSize(data):
    return (data & 0x7FFFFFFF)
    
def MakeChunkSize(data):
	return (data | 0x80000000)

def GetVersion(data):
    return struct_w3d.Version(major = (data)>>16, minor = (data) & 0xFFFF)
    
def MakeVersion(version):
	return (((version.major) << 16) | (version.minor))

def ReadString(file):
    bytes = []
    b = file.read(1)
    while ord(b) != 0:
        bytes.append(b)
        b = file.read(1)
    return (b"".join(bytes)).decode("utf-8")
    
def WriteString(file, string):
	file.write(bytes(string, 'UTF-8'))
	#write binary 0
	file.write(struct.pack('B', 0))
   
def ReadFixedString(file):
    return ((str(file.read(16)))[2:18]).split("\\")[0]
    
def WriteFixedString(file, string):
	#truncate the string to 16
	nullbytes = 16-len(string)
	if(nullbytes<0):
		print("Warning: Fixed string is too long")

	file.write(bytes(string, 'UTF-8'))
	for i in range(nullbytes):
		file.write(struct.pack("B", 0))

def ReadLongFixedString(file):
    return ((str(file.read(32)))[2:34]).split("\\")[0]
    
def WriteLongFixedString(file, string):
	#truncate the string to 32
	nullbytes = 32-len(string)
	if(nullbytes<0):
		print("Warning: Fixed string is too long")

	file.write(bytes(string, 'UTF-8'))
	for i in range(nullbytes):
		file.write(struct.pack("B", 0))
 
def ReadRGBA(file):
    return struct_w3d.RGBA(r=ord(file.read(1)), g=ord(file.read(1)), b=ord(file.read(1)), a=ord(file.read(1)))
    
def WriteRGBA(file, rgba):
	file.write(struct.pack("B", rgba.r))
	file.write(struct.pack("B", rgba.g))
	file.write(struct.pack("B", rgba.b))
	file.write(struct.pack("B", rgba.a))   
 
def ReadLong(file):
    return (struct.unpack("<L", file.read(4))[0])
    
def WriteLong(file, num):
	file.write(struct.pack("<L", num))

def ReadShort(file):
    return (struct.unpack("<H", file.read(2))[0])
    
def WriteShort(file, num):
	file.write(struct.pack("<H", num))

def ReadUnsignedShort(file):
    return (struct.unpack("<h", file.read(2))[0])  
    
def ReadFloat(file):
    return (struct.unpack("<f", file.read(4))[0])

def ReadLongArray(file,chunkEnd):
    LongArray = []
    while file.tell() < chunkEnd:
        LongArray.append(ReadLong(file))
    return LongArray
    
def WriteLongArray(file, array):
	for a in array:
		WriteLong(file, a)
    
def ReadVector(file):
    return Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
    
def WriteVector(file, vec):
	WriteFloat(file, vec[0])
	WriteFloat(file, vec[1])
	WriteFloat(file, vec[2])

def ReadQuaternion(file):
    quat = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    #change order from xyzw to wxyz
    return Quaternion((quat[3], quat[0], quat[1], quat[2]))
    
def WriteQuaternion(file, quat):
	#changes the order from wxyz to xyzw
	WriteFloat(file, quat[1])
	WriteFloat(file, quat[2])
	WriteFloat(file, quat[3])
	WriteFloat(file, quat[0])
