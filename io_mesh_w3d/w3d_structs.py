# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

from mathutils import Vector, Quaternion
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.import_utils_w3d import *
from io_mesh_w3d.w3d_adaptive_delta import *


class Struct:
    def __init__(self, *argv, **argd):
        if len(argd):
            # Update by dictionary
            self.__dict__.update(argd)
        else:
            # Update by position
            attrs = filter(lambda x: x[0:2] != "__", dir(self))
            for n in range(len(argv)):
                setattr(self, attrs[n], argv[n])


HEAD = 8  # 4(long = chunk_type) + 4 (long = chunk_size)

#######################################################################################
# Basic Structs
#######################################################################################


class RGBA(Struct):
    r = 0
    g = 0
    b = 0
    a = 0

    @staticmethod
    def read(file):
        return RGBA(r=ord(file.read(1)),
                    g=ord(file.read(1)),
                    b=ord(file.read(1)),
                    a=ord(file.read(1)))

    @staticmethod
    def read_f(file):
        return RGBA(r=read_float(file),
                    g=read_float(file),
                    b=read_float(file),
                    a=read_float(file))

    def write(self, file):
        file.write(struct.pack("B", self.r))
        file.write(struct.pack("B", self.g))
        file.write(struct.pack("B", self.b))
        file.write(struct.pack("B", self.a))

    def write_f(self, file):
        write_float(file, self.r)
        write_float(file, self.g)
        write_float(file, self.b)
        write_float(file, self.a)


class Version(Struct):
    major = 5
    minor = 0

    @staticmethod
    def read(file):
        data = read_ulong(file)
        return Version(major=data >> 16,
                       minor=data & 0xFFFF)

    def write(self, file):
        write_ulong(file, (self.major << 16) | self.minor)


#######################################################################################
# Hierarchy
#######################################################################################


W3D_CHUNK_HIERARCHY_HEADER = 0x00000101


class HierarchyHeader(Struct):
    version = Version()
    name = ""
    numPivots = 0
    centerPos = Vector((0.0, 0.0, 0.0))

    @staticmethod
    def read(file):
        return HierarchyHeader(
            version=Version.read(file),
            name=read_fixed_string(file),
            numPivots=read_ulong(file),
            centerPos=read_vector(file))

    @staticmethod
    def size_in_bytes():
        return 36

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_HIERARCHY_HEADER, self.size_in_bytes())
        self.version.write(file)
        write_fixed_string(file, self.name)
        write_ulong(file, self.numPivots)
        write_vector(file, self.centerPos)


W3D_CHUNK_PIVOTS = 0x00000102


class HierarchyPivot(Struct):
    name = ""
    parentID = -1
    translation = Vector((0.0, 0.0, 0.0))
    eulerAngles = Vector((0.0, 0.0, 0.0))
    rotation = Quaternion((1.0, 0.0, 0.0, 0.0))

    @staticmethod
    def read(file):
        return HierarchyPivot(
            name=read_fixed_string(file),
            parentID=read_long(file),
            translation=read_vector(file),
            eulerAngles=read_vector(file),
            rotation=read_quaternion(file))

    def size_in_bytes(self):
        return 60

    def write(self, file):
        write_fixed_string(file, self.name)
        write_long(file, self.parentID)
        write_vector(file, self.translation)
        write_vector(file, self.eulerAngles)
        write_quaternion(file, self.rotation)


W3D_CHUNK_HIERARCHY = 0x00000100
W3D_CHUNK_PIVOT_FIXUPS = 0x00000103


class Hierarchy(Struct):
    header = HierarchyHeader()
    pivots = []
    pivot_fixups = []

    @staticmethod
    def read(self, file, chunk_end):
        result = Hierarchy(
            pivots=[],
            pivot_fixups=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_HIERARCHY_HEADER:
                result.header = HierarchyHeader.read(file)
            elif chunk_type == W3D_CHUNK_PIVOTS:
                result.pivots = read_array(
                    file, subchunk_end, HierarchyPivot.read)
            elif chunk_type == W3D_CHUNK_PIVOT_FIXUPS:
                result.pivot_fixups = read_array(
                    file, subchunk_end, read_vector)
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def pivotsSize(self):
        size = 0
        for pivot in self.pivots:
            size += pivot.size_in_bytes()
        return size

    def pivotFixupsSize(self):
        size = 0
        for _ in self.pivot_fixups:
            size += 12  # size in bytes
        return size

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        size += HEAD + self.pivotsSize()
        if self.pivot_fixups:
            size += HEAD + self.pivotFixupsSize()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_HIERARCHY, self.size_in_bytes())
        self.header.write(file)
        write_chunk_head(file, W3D_CHUNK_PIVOTS, self.pivotsSize())
        for pivot in self.pivots:
            pivot.write(file)

        if self.pivot_fixups:
            write_chunk_head(file, W3D_CHUNK_PIVOT_FIXUPS,
                             self.pivotFixupsSize())
            for fixup in self.pivot_fixups:
                write_vector(file, fixup)


#######################################################################################
# Animation
#######################################################################################


W3D_CHUNK_ANIMATION_HEADER = 0x00000201


class AnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchy_name = ""
    num_frames = 0
    frame_rate = 0

    @staticmethod
    def read(file):
        return AnimationHeader(
            version=Version.read(file),
            name=read_fixed_string(file),
            hierarchy_name=read_fixed_string(file),
            num_frames=read_ulong(file),
            frame_rate=read_ulong(file))

    def size_in_bytes(self):
        return 44

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_ANIMATION_HEADER, self.size_in_bytes())
        self.version.write(file)
        write_fixed_string(file, self.name)
        write_fixed_string(file, self.hierarchy_name)
        write_ulong(file, self.num_frames)
        write_ulong(file, self.frame_rate)


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel(Struct):
    firstFrame = 0
    lastFrame = 0
    vectorLen = 0
    type = 0
    pivot = 0
    unknown = 0
    data = []

    @staticmethod
    def read(file, chunk_end):
        result = AnimationChannel(
            firstFrame=read_ushort(file),
            lastFrame=read_ushort(file),
            vectorLen=read_ushort(file),
            type=read_ushort(file),
            pivot=read_ushort(file),
            unknown=read_ushort(file),
            data=[])

        if result.vectorLen == 1:
            result.data = read_array(file, chunk_end, read_float)
        elif result.vectorLen == 4:
            result.data = read_array(file, chunk_end, read_quaternion)
        return result

    def size_in_bytes(self):
        return 12 + (len(self.data) * self.vectorLen) * 4

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_ANIMATION_CHANNEL, self.size_in_bytes())

        write_ushort(file, self.firstFrame)
        write_ushort(file, self.lastFrame)
        write_ushort(file, self.vectorLen)
        write_ushort(file, self.type)
        write_ushort(file, self.pivot)
        write_ushort(file, self.unknown)

        for d in self.data:
            if self.vectorLen == 1:
                write_float(file, d)
            else:
                write_quaternion(file, d)


W3D_CHUNK_ANIMATION = 0x00000200


class Animation(Struct):
    header = AnimationHeader()
    channels = []

    @staticmethod
    def read(self, file, chunk_end):
        result = Animation(channels=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_ANIMATION_HEADER:
                result.header = AnimationHeader.read(file)
            elif chunk_type == W3D_CHUNK_ANIMATION_CHANNEL:
                result.channels.append(
                    AnimationChannel.read(file, subchunk_end))
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for channel in self.channels:
            size += HEAD + channel.size_in_bytes()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_ANIMATION,
                         self.size_in_bytes(), hasSubChunks=True)
        self.header.write(file)

        for channel in self.channels:
            channel.write(file)


#######################################################################################
# Compressed Animation
#######################################################################################


W3D_CHUNK_COMPRESSED_ANIMATION_HEADER = 0x00000281


class CompressedAnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchy_name = ""
    num_frames = 0
    frame_rate = 0
    flavor = 0

    @staticmethod
    def read(file):
        return CompressedAnimationHeader(
            version=Version.read(file),
            name=read_fixed_string(file),
            hierarchy_name=read_fixed_string(file),
            num_frames=read_ulong(file),
            frame_rate=read_ushort(file),
            flavor=read_ushort(file))


class TimeCodedDatum(Struct):
    timeCode = 0
    nonInterpolated = False
    value = None

    @staticmethod
    def read(file, type):
        result = TimeCodedDatum(
            timeCode=read_long(file),
            value=read_channel_value(file, type))

        if (result.timeCode >> 31) == 1:
            result.timeCode &= ~(1 << 31)
            result.nonInterpolated = True
        return result


class TimeCodedBitDatum(Struct):
    timeCode = 0
    value = None

    @staticmethod
    def read(file):
        result = TimeCodedBitDatum(
            timeCode=read_long(file),
            value=False)

        if (result.timeCode >> 31) == 1:
            result.value = True
            result.timeCode &= ~(1 << 31)
        return result


class TimeCodedAnimationChannel(Struct):
    numTimeCodes = 0
    pivot = -1
    vectorLen = 0
    type = 0
    timeCodes = []

    @staticmethod
    def read(file):
        result = TimeCodedAnimationChannel(
            numTimeCodes=read_ulong(file),
            pivot=read_ushort(file),
            vectorLen=read_ubyte(file),
            type=read_ubyte(file),
            timeCodes=[])

        for _ in range(result.numTimeCodes):
            result.timeCodes.append(TimeCodedDatum.read(file, result.type))
        return result


class AdaptiveDeltaAnimationChannel(Struct):
    numTimeCodes = 0
    pivot = -1
    vectorLen = 0
    type = 0
    scale = 0
    data = []

    @staticmethod
    def read(file):
        result = AdaptiveDeltaAnimationChannel(
            numTimeCodes=read_ulong(file),
            pivot=read_ushort(file),
            vectorLen=read_ubyte(file),
            type=read_ubyte(file),
            scale=read_short(file),
            data=[])

        result.data = AdaptiveDeltaData.read(file, result, 4)

        file.read(3)  # read unknown bytes at the end
        return result


class AdaptiveDeltaMotionAnimationChannel(Struct):
    scale = 0.0
    initialValue = None
    data = []

    @staticmethod
    def read(file, channel, bits):
        result = AdaptiveDeltaMotionAnimationChannel(
            scale=read_float(file),
            data=[])

        data = AdaptiveDeltaData.read(file, channel, bits)
        result.data = decode(data, channel, result.scale)
        return result


class AdaptiveDeltaBlock(Struct):
    vectorIndex = 0
    blockIndex = 0
    deltaBytes = []

    @staticmethod
    def read(file, vecIndex, bits):
        result = AdaptiveDeltaBlock(
            vectorIndex=vecIndex,
            blockIndex=read_ubyte(file),
            deltaBytes=[])

        result.deltaBytes = read_fixed_array(file, bits * 2, read_byte)
        return result


class AdaptiveDeltaData(Struct):
    initialValue = None
    deltaBlocks = []
    bitCount = 0

    @staticmethod
    def read(file, channel, bits):
        result = AdaptiveDeltaData(
            initialValue=read_channel_value(file, channel.type),
            deltaBlocks=[],
            bitCount=bits)

        count = (channel.numTimeCodes + 15) >> 4

        for _ in range(count):
            for j in range(channel.vectorLen):
                result.deltaBlocks.append(
                    AdaptiveDeltaBlock.read(file, j, bits))
        return result


class TimeCodedBitChannel(Struct):
    numTimeCodes = 0
    pivot = 0
    type = 0
    defaultValue = False
    data = []

    @staticmethod
    def read(file):
        result = TimeCodedBitChannel(
            numTimeCodes=read_long(file),
            pivot=read_short(file),
            type=read_ubyte(file),
            defaultValue=read_ubyte(file),
            data=[])

        for _ in range(result.numTimeCodes):
            result.data.append(TimeCodedBitDatum.read(file))
        return result


class MotionChannel(Struct):
    deltaType = 0
    vectorLen = 0
    type = 0
    numTimeCodes = 0
    pivot = 0
    data = []

    # TODO: find a nice way for this
    @staticmethod
    def read_time_coded_data(file, channel):
        result = []

        for x in range(channel.numTimeCodes):
            datum = TimeCodedDatum(
                timeCode=read_short(file))
            result.append(datum)

        if channel.numTimeCodes % 2 != 0:
            read_short(file)  # alignment

        for x in range(channel.numTimeCodes):
            result[x].value = read_channel_value(file, channel.type)
        return result

    @staticmethod
    def read(file, chunk_end):
        read_ubyte(file)  # zero

        result = MotionChannel(
            deltaType=read_ubyte(file),
            vectorLen=read_ubyte(file),
            type=read_ubyte(file),
            numTimeCodes=read_short(file),
            pivot=read_short(file),
            data=[])

        if result.deltaType == 0:
            result.data = MotionChannel.read_time_coded_data(file, result)
        elif result.deltaType == 1:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(
                file, result, 4)
        elif result.deltaType == 2:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(
                file, result, 8)
        else:
            print("unknown motion deltatype!!")
        return result


W3D_CHUNK_COMPRESSED_ANIMATION = 0x00000280
W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL = 0x00000282
W3D_CHUNK_COMPRESSED_BIT_CHANNEL = 0x00000283
W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL = 0x00000284


class CompressedAnimation(Struct):
    header = CompressedAnimationHeader()
    timeCodedChannels = []
    adaptiveDeltaChannels = []
    timeCodedBitChannels = []
    motionChannels = []

    @staticmethod
    def read(self, file, chunk_end):
        result = CompressedAnimation(
            timeCodedChannels=[],
            adaptiveDeltaChannels=[],
            timeCodedBitChannels=[],
            motionChannels=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_HEADER:
                result.header = CompressedAnimationHeader.read(file)
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL:
                if result.header.flavor == 0:
                    result.timeCodedChannels.append(
                        TimeCodedAnimationChannel.read(file))
                elif result.header.flavor == 1:
                    result.adaptiveDeltaChannels.append(
                        AdaptiveDeltaAnimationChannel.read(file))
                else:
                    skip_unknown_chunk(self, file, chunk_type, chunk_size)
            elif chunk_type == W3D_CHUNK_COMPRESSED_BIT_CHANNEL:
                result.timeCodedBitChannels.append(
                    TimeCodedBitChannel.read(file))
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL:
                result.motionChannels.append(
                    MotionChannel.read(file, subchunk_end))
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

#######################################################################################
# HLod
#######################################################################################


W3D_CHUNK_HLOD_HEADER = 0x00000701


class HLodHeader(Struct):
    version = Version()
    lodCount = 1
    modelName = ""
    hierarchy_name = ""

    @staticmethod
    def read(file):
        return HLodHeader(
            version=Version.read(file),
            lodCount=read_ulong(file),
            modelName=read_fixed_string(file),
            hierarchy_name=read_fixed_string(file))

    def size_in_bytes(self):
        return 40

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_HLOD_HEADER, self.size_in_bytes())
        self.version.write(file)
        write_ulong(file, self.lodCount)
        write_fixed_string(file, self.modelName)
        write_fixed_string(file, self.hierarchy_name)


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703


class HLodArrayHeader(Struct):
    modelCount = 0
    maxScreenSize = 0.0

    @staticmethod
    def read(file):
        return HLodArrayHeader(
            modelCount=read_ulong(file),
            maxScreenSize=read_float(file))

    def size_in_bytes(self):
        return HEAD

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER,
                         self.size_in_bytes())
        write_ulong(file, self.modelCount)
        write_float(file, self.maxScreenSize)


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    boneIndex = 0
    name = ""

    @staticmethod
    def read(file):
        return HLodSubObject(
            boneIndex=read_ulong(file),
            name=read_long_fixed_string(file))

    @staticmethod
    def size_in_bytes():
        return 36

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_HLOD_SUB_OBJECT, self.size_in_bytes())
        write_ulong(file, self.boneIndex)
        write_long_fixed_string(file, self.name)


W3D_CHUNK_HLOD_LOD_ARRAY = 0x00000702


class HLodArray(Struct):
    header = HLodArrayHeader()
    subObjects = []

    @staticmethod
    def read(self, file, chunk_end):
        result = HLodArray(
            header=None,
            subObjects=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER:
                result.header = HLodArrayHeader.read(file)
            elif chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT:
                result.subObjects.append(HLodSubObject.read(file))
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for obj in self.subObjects:
            size += HEAD + obj.size_in_bytes()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_HLOD_LOD_ARRAY,
                         self.size_in_bytes(), hasSubChunks=True)
        self.header.write(file)
        for obj in self.subObjects:
            obj.write(file)


W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = HLodHeader()
    lodArray = HLodArray()

    @staticmethod
    def read(self, file, chunk_end):
        result = HLod(
            header=None,
            lodArray=None
        )

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_HLOD_HEADER:
                result.header = HLodHeader.read(file)
            elif chunk_type == W3D_CHUNK_HLOD_LOD_ARRAY:
                result.lodArray = HLodArray.read(self, file, subchunk_end)
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        size += HEAD + self.lodArray.size_in_bytes()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_HLOD,
                         self.size_in_bytes(), hasSubChunks=True)
        self.header.write(file)
        self.lodArray.write(file)


#######################################################################################
# Box
#######################################################################################


W3D_CHUNK_BOX = 0x00000740


class Box(Struct):
    version = Version()
    boxType = 0
    collisionTypes = 0
    name = ""
    color = RGBA()
    center = Vector((0.0, 0.0, 0.0))
    extend = Vector((0.0, 0.0, 0.0))

    @staticmethod
    def read(file):
        ver = Version.read(file)
        flags = read_ulong(file)
        return Box(
            version=ver,
            boxType=(flags & 0b11),
            collisionTypes=(flags & 0xFF0),
            name=read_long_fixed_string(file),
            color=RGBA.read(file),
            center=read_vector(file),
            extend=read_vector(file))

    def size_in_bytes(self):
        return 68

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_BOX, self.size_in_bytes())

        # TODO: fix version writing
        # self.version.write(file)
        write_long(file, 9)

        write_ulong(file, (self.collisionTypes & 0xFF) | (self.boxType & 0b11))
        write_long_fixed_string(file, self.name)
        self.color.write(file)
        write_vector(file, self.center)
        write_vector(file, self.extend)


#######################################################################################
# Texture
#######################################################################################


W3D_CHUNK_TEXTURE_INFO = 0x00000033


class TextureInfo(Struct):
    attributes = 0
    animationType = 0
    frameCount = 0
    frame_rate = 0.0

    @staticmethod
    def read(file):
        return TextureInfo(
            attributes=read_ushort(file),
            animationType=read_ushort(file),
            frameCount=read_ulong(file),
            frame_rate=read_float(file))

    @staticmethod
    def size_in_bytes():
        return 12

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_TEXTURE_INFO, self.size_in_bytes())
        write_ushort(file, self.attributes)
        write_ushort(file, self.animationType)
        write_ulong(file, self.frameCount)
        write_float(file, self.frame_rate)


W3D_CHUNK_TEXTURE = 0x00000031
W3D_CHUNK_TEXTURE_NAME = 0x00000032


class Texture(Struct):
    name = ""
    textureInfo = None

    @staticmethod
    def read(self, file, chunk_end):
        result = Texture(textureInfo=None)

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_TEXTURE_NAME:
                result.name = read_string(file)
            elif chunk_type == W3D_CHUNK_TEXTURE_INFO:
                result.textureInfo = TextureInfo.read(file)
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + string_size(self.name)
        if self.textureInfo is not None:
            size += HEAD + self.textureInfo.size_in_bytes()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_TEXTURE,
                         self.size_in_bytes(), hasSubChunks=True)
        write_chunk_head(file, W3D_CHUNK_TEXTURE_NAME, string_size(self.name))
        write_string(file, self.name)

        if self.textureInfo is not None:
            write_chunk_head(file, W3D_CHUNK_TEXTURE_INFO,
                             self.textureInfo.size_in_bytes())
            self.textureInfo.write(file)


#######################################################################################
# Material
#######################################################################################


W3D_CHUNK_TEXTURE_STAGE = 0x00000048
W3D_CHUNK_TEXTURE_IDS = 0x00000049
W3D_CHUNK_STAGE_TEXCOORDS = 0x0000004A
W3D_CHUNK_PER_FACE_TEXCOORD_IDS = 0x0000004B


class TextureStage(Struct):
    txIds = []
    perFaceTxCoords = []
    txCoords = []

    @staticmethod
    def read(file, chunk_end):
        result = TextureStage(
            txIds=[],
            perFaceTxCoords=[],
            txCoords=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_TEXTURE_IDS:
                result.txIds = read_array(file, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_STAGE_TEXCOORDS:
                result.txCoords = read_array(file, subchunk_end, read_vector2)
            elif chunk_type == W3D_CHUNK_PER_FACE_TEXCOORD_IDS:
                result.perFaceTxCoords = read_array(
                    file, subchunk_end, read_vector)
            else:
                skip_unknown_chunk(None, file, chunk_type, chunk_size)
        return result

    def txIdsSize(self):
        return len(self.txIds) * 4

    def perFaceTxCoordsSize(self):
        return len(self.perFaceTxCoords) * 12

    def txCoordsSize(self):
        return len(self.txCoords) * 8

    def size_in_bytes(self):
        size = 0
        if self.txIds:
            size += HEAD + self.txIdsSize()
        if self.txCoords:
            size += HEAD + self.txCoordsSize()
        if self.perFaceTxCoords:
            size += HEAD + self.perFaceTxCoordsSize()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_TEXTURE_STAGE,
                         self.size_in_bytes(), hasSubChunks=True)

        if self.txIds:
            write_chunk_head(file, W3D_CHUNK_TEXTURE_IDS, self.txIdsSize())
            write_array(file, self.txIds, write_long)

        if self.txCoords:
            write_chunk_head(file, W3D_CHUNK_STAGE_TEXCOORDS,
                             self.txCoordsSize())
            write_array(file, self.txCoords, write_vector2)

        if self.perFaceTxCoords:
            write_chunk_head(file, W3D_CHUNK_PER_FACE_TEXCOORD_IDS,
                             self.perFaceTxCoordsSize())
            write_array(file, self.perFaceTxCoords, write_vector)


W3D_CHUNK_MATERIAL_PASS = 0x00000038
W3D_CHUNK_VERTEX_MATERIAL_IDS = 0x00000039
W3D_CHUNK_SHADER_IDS = 0x0000003A
W3D_CHUNK_DCG = 0x0000003B
W3D_CHUNK_DIG = 0x0000003C
W3D_CHUNK_SCG = 0x0000003E
W3D_CHUNK_SHADER_MATERIAL_ID = 0x3F


class MaterialPass(Struct):
    vertexMaterialIds = []
    shaderIds = []
    dcg = []
    dig = []
    scg = []
    shaderMaterialIds = []
    txStages = []
    txCoords = []

    @staticmethod
    def read(file, chunk_end):
        result = MaterialPass(
            vertexMaterialIds=[],
            shaderIds=[],
            dcg=[],
            dig=[],
            scg=[],
            shaderMaterialIds=[],
            txStages=[],
            txCoords=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_VERTEX_MATERIAL_IDS:
                result.vertexMaterialIds = read_array(
                    file, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_SHADER_IDS:
                result.shaderIds = read_array(file, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_DCG:
                result.dcg = read_array(file, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_DIG:
                result.dig = read_array(file, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_SCG:
                result.scg = read_array(file, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_ID:
                result.shaderMaterialIds = read_array(
                    file, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_TEXTURE_STAGE:
                result.txStages.append(
                    TextureStage.read(file, subchunk_end))
            elif chunk_type == W3D_CHUNK_STAGE_TEXCOORDS:
                result.txCoords = read_array(file, subchunk_end, read_vector2)
            else:
                skip_unknown_chunk(None, file, chunk_type, chunk_size)
        return result

    def vertexMaterialIdsSize(self):
        return len(self.vertexMaterialIds) * 4

    def shaderIdsSize(self):
        return len(self.shaderIds) * 4

    def dcgSize(self):
        return len(self.dcg) * 4

    def digSize(self):
        return len(self.dig) * 4

    def scgSize(self):
        return len(self.scg) * 4

    def shaderMaterialIdsSize(self):
        return len(self.shaderMaterialIds) * 4

    def txStagesSize(self):
        size = 0
        for stage in self.txStages:
            size += HEAD + stage.size_in_bytes()
        return size

    def txCoordsSize(self):
        return len(self.txCoords) * 8

    def size_in_bytes(self):
        size = 0
        if self.vertexMaterialIds:
            size = HEAD + self.vertexMaterialIdsSize()
        if self.shaderIds:
            size += HEAD + self.shaderIdsSize()
        if self.dcg:
            size += HEAD + self.dcgSize()
        if self.dig:
            size += HEAD + self.digSize()
        if self.scg:
            size += HEAD + self.scgSize()
        if self.shaderMaterialIds:
            size += HEAD + self.shaderMaterialIdsSize()
        if self.txStages:
            size += self.txStagesSize()
        if self.txCoords:
            size += HEAD + self.txCoordsSize()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_MATERIAL_PASS,
                         self.size_in_bytes(), hasSubChunks=True)

        if self.vertexMaterialIds:
            write_chunk_head(file, W3D_CHUNK_VERTEX_MATERIAL_IDS,
                             self.vertexMaterialIdsSize())
            write_array(file, self.vertexMaterialIds, write_ulong)
        if self.shaderIds:
            write_chunk_head(file, W3D_CHUNK_SHADER_IDS, self.shaderIdsSize())
            write_array(file, self.shaderIds, write_ulong)
        if self.dcg:
            write_chunk_head(file, W3D_CHUNK_DCG, self.dcgSize())
            for d in self.dcg:
                d.write(file)
        if self.dig:
            write_chunk_head(file, W3D_CHUNK_DIG, self.digSize())
            for d in self.dig:
                d.write(file)
        if self.scg:
            write_chunk_head(file, W3D_CHUNK_SCG, self.scgSize())
            for d in self.scg:
                d.write(file)
        if self.shaderMaterialIds:
            write_chunk_head(file, W3D_CHUNK_SHADER_MATERIAL_ID,
                             self.shaderMaterialIdsSize())
            write_array(file, self.shaderMaterialIds, write_ulong)
        if self.txStages:
            for txStage in self.txStages:
                txStage.write(file)
        if self.txCoords:
            write_chunk_head(file, W3D_CHUNK_STAGE_TEXCOORDS,
                             self.txCoordsSize())
            write_array(file, self.txCoords, write_vector2)


W3D_CHUNK_MATERIAL_INFO = 0x00000028


class MaterialInfo(Struct):
    passCount = 1
    vertMatlCount = 0
    shaderCount = 0
    textureCount = 0

    @staticmethod
    def read(file):
        return MaterialInfo(
            passCount=read_ulong(file),
            vertMatlCount=read_ulong(file),
            shaderCount=read_ulong(file),
            textureCount=read_ulong(file))

    @staticmethod
    def size_in_bytes():
        return 16

    def write(self, file):
        write_ulong(file, self.passCount)
        write_ulong(file, self.vertMatlCount)
        write_ulong(file, self.shaderCount)
        write_ulong(file, self.textureCount)


W3D_CHUNK_VERTEX_MATERIAL_INFO = 0x0000002D


class VertexMaterialInfo(Struct):
    attributes = 0
    ambient = RGBA()  # alpha is only padding in this and below
    diffuse = RGBA()
    specular = RGBA()
    emissive = RGBA()
    shininess = 0.0
    opacity = 0.0
    translucency = 0.0

    @staticmethod
    def read(file):
        return VertexMaterialInfo(
            attributes=read_long(file),
            ambient=RGBA.read(file),
            diffuse=RGBA.read(file),
            specular=RGBA.read(file),
            emissive=RGBA.read(file),
            shininess=read_float(file),
            opacity=read_float(file),
            translucency=read_float(file))

    @staticmethod
    def size_in_bytes():
        return 32

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_VERTEX_MATERIAL_INFO,
                         self.size_in_bytes())
        write_long(file, self.attributes)
        self.ambient.write(file)
        self.diffuse.write(file)
        self.specular.write(file)
        self.emissive.write(file)
        write_float(file, self.shininess)
        write_float(file, self.opacity)
        write_float(file, self.translucency)


W3D_CHUNK_VERTEX_MATERIAL = 0x0000002B
W3D_CHUNK_VERTEX_MATERIAL_NAME = 0x0000002C
W3D_CHUNK_VERTEX_MAPPER_ARGS0 = 0x0000002E
W3D_CHUNK_VERTEX_MAPPER_ARGS1 = 0x0000002F


class VertexMaterial(Struct):
    vmName = ""
    vmInfo = VertexMaterialInfo()
    vmArgs0 = ""
    vmArgs1 = ""

    @staticmethod
    def read(self, file, chunk_end):
        result = VertexMaterial()

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_VERTEX_MATERIAL_NAME:
                result.vmName = read_string(file)
            elif chunk_type == W3D_CHUNK_VERTEX_MATERIAL_INFO:
                result.vmInfo = VertexMaterialInfo.read(file)
            elif chunk_type == W3D_CHUNK_VERTEX_MAPPER_ARGS0:
                result.vmArgs0 = read_string(file)
            elif chunk_type == W3D_CHUNK_VERTEX_MAPPER_ARGS1:
                result.vmArgs1 = read_string(file)
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + string_size(self.vmName)
        size += HEAD + self.vmInfo.size_in_bytes()
        size += HEAD + string_size(self.vmArgs0)
        size += HEAD + string_size(self.vmArgs1)
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_VERTEX_MATERIAL,
                         self.size_in_bytes(), hasSubChunks=True)
        write_chunk_head(file, W3D_CHUNK_VERTEX_MATERIAL_NAME,
                         string_size(self.vmName))
        write_string(file, self.vmName)
        self.vmInfo.write(file)
        write_chunk_head(file, W3D_CHUNK_VERTEX_MAPPER_ARGS0,
                         string_size(self.vmArgs0))
        write_string(file, self.vmArgs0)
        write_chunk_head(file, W3D_CHUNK_VERTEX_MAPPER_ARGS1,
                         string_size(self.vmArgs1))
        write_string(file, self.vmArgs1)


#######################################################################################
# Vertices
#######################################################################################


class MeshVertexInfluence(Struct):
    boneIdx = 0
    xtraIdx = 0
    boneInf = 0.0
    xtraInf = 0.0

    @staticmethod
    def read(file):
        return MeshVertexInfluence(
            boneIdx=read_ushort(file),
            xtraIdx=read_ushort(file),
            boneInf=read_ushort(file)/100,
            xtraInf=read_ushort(file)/100)

    @staticmethod
    def size_in_bytes():
        return 8

    def write(self, file):
        write_ushort(file, self.boneIdx)
        write_ushort(file, self.xtraIdx)
        write_ushort(file, int(self.boneInf * 100))
        write_ushort(file, int(self.xtraInf * 100))


#######################################################################################
# Triangle
#######################################################################################


class MeshTriangle(Struct):
    vertIds = []
    surfaceType = 13
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0

    @staticmethod
    def read(file):
        return MeshTriangle(
            vertIds=(read_ulong(file), read_ulong(file), read_ulong(file)),
            surfaceType=read_ulong(file),
            normal=read_vector(file),
            distance=read_float(file))

    @staticmethod
    def size_in_bytes():
        return 32

    def write(self, file):
        write_ulong(file, self.vertIds[0])
        write_ulong(file, self.vertIds[1])
        write_ulong(file, self.vertIds[2])
        write_ulong(file, self.surfaceType)
        write_vector(file, self.normal)
        write_float(file, self.distance)


#######################################################################################
# Shader
#######################################################################################


class MeshShader(Struct):
    depthCompare = 3
    depthMask = 1
    colorMask = 0
    destBlend = 0
    fogFunc = 2
    priGradient = 1
    secGradient = 0
    srcBlend = 1
    texturing = 1
    detailColorFunc = 0
    detailAlphaFunc = 0
    shaderPreset = 2
    alphaTest = 0
    postDetailColorFunc = 0
    postDetailAlphaFunc = 0
    pad = 2

    @staticmethod
    def read(file):
        return MeshShader(
            depthCompare=read_ubyte(file),
            depthMask=read_ubyte(file),
            colorMask=read_ubyte(file),
            destBlend=read_ubyte(file),
            fogFunc=read_ubyte(file),
            priGradient=read_ubyte(file),
            secGradient=read_ubyte(file),
            srcBlend=read_ubyte(file),
            texturing=read_ubyte(file),
            detailColorFunc=read_ubyte(file),
            detailAlphaFunc=read_ubyte(file),
            shaderPreset=read_ubyte(file),
            alphaTest=read_ubyte(file),
            postDetailColorFunc=read_ubyte(file),
            postDetailAlphaFunc=read_ubyte(file),
            pad=read_ubyte(file))

    @staticmethod
    def size_in_bytes():
        return 16

    def write(self, file):
        write_ubyte(file, self.depthCompare)
        write_ubyte(file, self.depthMask)
        write_ubyte(file, self.colorMask)
        write_ubyte(file, self.destBlend)
        write_ubyte(file, self.fogFunc)
        write_ubyte(file, self.priGradient)
        write_ubyte(file, self.secGradient)
        write_ubyte(file, self.srcBlend)
        write_ubyte(file, self.texturing)
        write_ubyte(file, self.detailColorFunc)
        write_ubyte(file, self.detailAlphaFunc)
        write_ubyte(file, self.shaderPreset)
        write_ubyte(file, self.alphaTest)
        write_ubyte(file, self.postDetailColorFunc)
        write_ubyte(file, self.postDetailAlphaFunc)
        write_ubyte(file, self.pad)


#######################################################################################
# Shader Material
#######################################################################################


W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52


class ShaderMaterialHeader(Struct):
    number = 0
    typeName = ""
    reserved = 0

    @staticmethod
    def read(file):
        return ShaderMaterialHeader(
            number=read_ubyte(file),
            typeName=read_long_fixed_string(file),
            reserved=read_long(file))

    @staticmethod
    def size_in_bytes():
        return 37

    def write(self, file):
        write_chunk_head(
            file, W3D_CHUNK_SHADER_MATERIAL_HEADER, self.size_in_bytes())
        write_ubyte(file, self.number)
        write_long_fixed_string(file, self.typeName)
        write_long(file, self.reserved)


W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x53


class ShaderMaterialProperty(Struct):
    type = 0
    name = ""
    numChars = 0
    value = None

    @staticmethod
    def read(file):
        result = ShaderMaterialProperty(
            type=read_long(file),
            numChars=read_long(file),
            name=read_string(file))

        if result.type == 1:
            read_long(file)  # num available chars
            result.value = read_string(file)
        elif result.type == 2:
            result.value = read_float(file)
        elif result.type == 4:
            result.value = read_vector(file)
        elif result.type == 5:
            result.value = RGBA.read_f(file)
        elif result.type == 6:
            result.value = read_long(file)
        elif result.type == 7:
            result.value = read_ubyte(file)
        return result

    def size_in_bytes(self):
        size = 8 + string_size(self.name)
        if self.type == 1:
            size += 4 + string_size(self.value)
        elif self.type == 2:
            size += 4
        elif self.type == 4:
            size += 12
        elif self.type == 5:
            size += 16
        elif self.type == 6:
            size += 4
        elif self.type == 7:
            size += 1
        return size

    def write(self, file):
        write_chunk_head(
            file, W3D_CHUNK_SHADER_MATERIAL_PROPERTY, self.size_in_bytes())
        write_long(file, self.type)
        write_long(file, self.numChars)
        write_string(file, self.name)

        if self.type == 1:
            write_long(file, string_size(self.value))
            write_string(file, self.value)
        elif self.type == 2:
            write_float(file, self.value)
        elif self.type == 4:
            write_vector(file, self.value)
        elif self.type == 5:
            self.value.write_f(file)
        elif self.type == 6:
            write_long(file, self.value)
        elif self.type == 7:
            write_ubyte(file, self.value)


W3D_CHUNK_SHADER_MATERIAL = 0x51


class ShaderMaterial(Struct):
    header = ShaderMaterialHeader()
    properties = []

    @staticmethod
    def read(self, file, chunk_end):
        result = ShaderMaterial(
            properties=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_SHADER_MATERIAL_HEADER:
                result.header = ShaderMaterialHeader.read(file)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_PROPERTY:
                result.properties.append(ShaderMaterialProperty.read(file))
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for prop in self.properties:
            size += HEAD + prop.size_in_bytes()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_SHADER_MATERIAL,
                         self.size_in_bytes(), hasSubChunks=True)
        self.header.write(file)
        for prop in self.properties:
            prop.write(file)


#######################################################################################
# AABBTree (Axis-aligned-bounding-box-tree)
#######################################################################################


W3D_CHUNK_AABBTREE_HEADER = 0x00000091


class AABBTreeHeader(Struct):
    nodeCount = 0
    polyCount = 0

    @staticmethod
    def read(file):
        result = AABBTreeHeader(
            nodeCount=read_ulong(file),
            poyCount=read_ulong(file))

        file.read(24)  # padding
        return result

    @staticmethod
    def size_in_bytes():
        return 8

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_AABBTREE_HEADER, self.size_in_bytes())
        write_ulong(file, self.nodeCount)
        write_ulong(file, self.polyCount)


class AABBTreeNode(Struct):
    min = Vector((0.0, 0.0, 0.0))
    max = Vector((0.0, 0.0, 0.0))
    frontOrPoly0 = 0
    backOrPolyCount = 0

    @staticmethod
    def read(file):
        return AABBTreeNode(
            min=read_vector(file),
            max=read_vector(file),
            frontOrPoly0=read_long(file),
            backOrPolyCount=read_long(file))

    @staticmethod
    def size_in_bytes():
        return 32

    def write(self, file):
        write_vector(file, self.min)
        write_vector(file, self.max)
        write_long(file, self.frontOrPoly0)
        write_long(file, self.backOrPolyCount)


W3D_CHUNK_AABBTREE = 0x00000090
W3D_CHUNK_AABBTREE_POLYINDICES = 0x00000092
W3D_CHUNK_AABBTREE_NODES = 0x00000093


class MeshAABBTree(Struct):
    header = AABBTreeHeader()
    polyIndices = []
    nodes = []

    @staticmethod
    def read(self, file, chunk_end):
        result = MeshAABBTree()

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_AABBTREE_HEADER:
                result.header = AABBTreeHeader.read(file)
            elif chunk_type == W3D_CHUNK_AABBTREE_POLYINDICES:
                result.polyIndices = read_array(file, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_AABBTREE_NODES:
                result.nodes = read_array(file, subchunk_end, AABBTreeNode.read)
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def polyIndicesSize(self):
        return len(self.polyIndices) * 4

    def nodesSize(self):
        size = 0
        for node in self.nodes:
            size += node.size_in_bytes()
        return size

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        if self.polyIndices:
            size += HEAD + self.polyIndicesSize()
        if self.nodes:
            size += HEAD + self.nodesSize()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_AABBTREE,
                         self.size_in_bytes(), hasSubChunks=True)
        self.header.write(file)

        if self.polyIndices:
            write_chunk_head(file, W3D_CHUNK_AABBTREE_POLYINDICES,
                             self.polyIndicesSize())
            write_array(file, self.polyIndices, write_long)
        if self.nodes:
            write_chunk_head(file, W3D_CHUNK_AABBTREE_NODES, self.nodesSize())
            for node in self.nodes:
                node.write(file)


#######################################################################################
# Mesh
#######################################################################################


W3D_CHUNK_MESH_HEADER = 0x0000001F


class MeshHeader(Struct):
    version = Version()
    attrs = 0
    meshName = ""
    containerName = ""
    faceCount = 0
    vertCount = 0
    matlCount = 0
    damageStageCount = 0
    sortLevel = 0
    prelitVersion = 0
    futureCount = 0
    vertChannelFlags = 3
    faceChannelFlags = 1
    minCorner = Vector((0.0, 0.0, 0.0))
    maxCorner = Vector((0.0, 0.0, 0.0))
    sphCenter = Vector((0.0, 0.0, 0.0))
    sphRadius = 0.0

    @staticmethod
    def read(file):
        return MeshHeader(
            version=Version.read(file),
            attrs=read_ulong(file),
            meshName=read_fixed_string(file),
            containerName=read_fixed_string(file),
            faceCount=read_ulong(file),
            vertCount=read_ulong(file),
            matlCount=read_ulong(file),
            damageStageCount=read_ulong(file),
            sortLevel=read_ulong(file),
            prelitVersion=read_ulong(file),
            futureCount=read_ulong(file),
            vertChannelFlags=read_ulong(file),
            faceChannelFlags=read_ulong(file),
            # bounding volumes
            minCorner=read_vector(file),
            maxCorner=read_vector(file),
            sphCenter=read_vector(file),
            sphRadius=read_float(file))

    @staticmethod
    def size_in_bytes():
        return 116

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_MESH_HEADER, self.size_in_bytes())
        self.version.write(file)
        write_ulong(file, self.attrs)
        write_fixed_string(file, self.meshName)
        write_fixed_string(file, self.containerName)
        write_ulong(file, self.faceCount)
        write_ulong(file, self.vertCount)
        write_ulong(file, self.matlCount)
        write_ulong(file, self.damageStageCount)
        write_ulong(file, self.sortLevel)
        write_ulong(file, self.prelitVersion)
        write_ulong(file, self.futureCount)
        write_ulong(file, self.vertChannelFlags)
        write_ulong(file, self.faceChannelFlags)
        write_vector(file, self.minCorner)
        write_vector(file, self.maxCorner)
        write_vector(file, self.sphCenter)
        write_float(file, self.sphRadius)


W3D_CHUNK_MESH = 0x00000000
W3D_CHUNK_VERTICES = 0x00000002
W3D_CHUNK_VERTICES_2 = 0xC00
W3D_CHUNK_VERTEX_NORMALS = 0x00000003
W3D_CHUNK_NORMALS_2 = 0xC01
W3D_CHUNK_MESH_USER_TEXT = 0x0000000C
W3D_CHUNK_VERTEX_INFLUENCES = 0x0000000E
W3D_CHUNK_TRIANGLES = 0x00000020
W3D_CHUNK_VERTEX_SHADE_INDICES = 0x00000022
W3D_CHUNK_SHADERS = 0x00000029
W3D_CHUNK_VERTEX_MATERIALS = 0x0000002A
W3D_CHUNK_TEXTURES = 0x00000030
W3D_CHUNK_SHADER_MATERIALS = 0x50
W3D_CHUNK_TANGENTS = 0x60
W3D_CHUNK_BITANGENTS = 0x61


class Mesh(Struct):
    header = MeshHeader()
    userText = ""
    verts = []
    normals = []
    vertInfs = []
    triangles = []
    shadeIds = []
    matInfo = None
    shaders = []
    vertMatls = []
    textures = []
    shaderMaterials = []
    materialPass = None
    aabbtree = None

    def read(self, file, chunk_end):
        result = Mesh(
            verts=[],
            normals=[],
            vertInfs=[],
            triangles=[],
            shadeIds=[],
            shaders=[],
            vertMatls=[],
            textures=[],
            shaderMaterials=[])

        while file.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(file)

            if chunk_type == W3D_CHUNK_VERTICES:
                result.verts = read_array(file, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_VERTICES_2:
                print("-> vertices 2 chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_VERTEX_NORMALS:
                result.normals = read_array(file, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_NORMALS_2:
                print("-> normals 2 chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_MESH_USER_TEXT:
                result.userText = read_string(file)
            elif chunk_type == W3D_CHUNK_VERTEX_INFLUENCES:
                result.vertInfs = read_array(
                    file, subchunk_end, MeshVertexInfluence.read)
            elif chunk_type == W3D_CHUNK_MESH_HEADER:
                result.header = MeshHeader.read(file)
            elif chunk_type == W3D_CHUNK_TRIANGLES:
                result.triangles = read_array(
                    file, subchunk_end, MeshTriangle.read)
            elif chunk_type == W3D_CHUNK_VERTEX_SHADE_INDICES:
                result.shadeIds = read_array(file, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_MATERIAL_INFO:
                result.matInfo = MaterialInfo.read(file)
            elif chunk_type == W3D_CHUNK_SHADERS:
                result.shaders = read_array(file, subchunk_end, MeshShader.read)
            elif chunk_type == W3D_CHUNK_VERTEX_MATERIALS:
                result.vertMatls = read_chunk_array(
                    self, file, subchunk_end, W3D_CHUNK_VERTEX_MATERIAL, VertexMaterial.read)
            elif chunk_type == W3D_CHUNK_TEXTURES:
                result.textures = read_chunk_array(
                    self, file, subchunk_end, W3D_CHUNK_TEXTURE, Texture.read)
            elif chunk_type == W3D_CHUNK_MATERIAL_PASS:
                result.materialPass = MaterialPass.read(
                    file, subchunk_end)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIALS:
                result.shaderMaterials = read_chunk_array(
                    self, file, subchunk_end, W3D_CHUNK_SHADER_MATERIAL, ShaderMaterial.read)
            elif chunk_type == W3D_CHUNK_TANGENTS:
                print("-> tangents chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_BITANGENTS:
                print("-> bitangents chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_AABBTREE:
                result.aabbtree = MeshAABBTree.read(self, file, subchunk_end)
            elif chunk_type == W3D_CHUNK_PRELIT_UNLIT:
                print("-> prelit unlit chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_VERTEX:
                print("-> prelit vertex chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS:
                print("-> prelit lightmap multi pass chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE:
                print("-> prelit lightmap multi texture chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_DEFORM:
                print("-> deform chunk is not supported")
                file.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PS2_SHADERS:
                print("-> ps2 shaders chunk is not supported")
                file.seek(chunk_size, 1)
            else:
                skip_unknown_chunk(self, file, chunk_type, chunk_size)
        return result

    def vertsSize(self):
        return len(self.verts) * 12

    def normalsSize(self):
        return len(self.normals) * 12

    def trisSize(self):
        size = 0
        for t in self.triangles:
            size += t.size_in_bytes()
        return size

    def vertInfsSize(self):
        size = 0
        for inf in self.vertInfs:
            size += inf.size_in_bytes()
        return size

    def shadersSize(self):
        size = 0
        for shader in self.shaders:
            size += shader.size_in_bytes()
        return size

    def texturesSize(self):
        size = 0
        for texture in self.textures:
            size += HEAD + texture.size_in_bytes()
        return size

    def shadeIdsSize(self):
        return len(self.shadeIds) * 4

    def shaderMaterialsSize(self):
        size = 0
        for shaderMat in self.shaderMaterials:
            size += HEAD + shaderMat.size_in_bytes()
        return size

    def vertMaterialsSize(self):
        size = 0
        for vertMat in self.vertMatls:
            size += HEAD + vertMat.size_in_bytes()
        return size

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        size += HEAD + self.vertsSize()
        size += HEAD + self.normalsSize()
        size += HEAD + self.trisSize()
        if self.vertInfs:
            size += HEAD + self.vertInfsSize()
        if self.shaders:
            size += HEAD + self.shadersSize()
        if self.textures:
            size += HEAD + self.texturesSize()
        if self.shadeIds:
            size += HEAD + self.shadeIdsSize()
        if self.shaderMaterials:
            size += HEAD + self.shaderMaterialsSize()
        if self.matInfo is not None:
            size += HEAD + self.matInfo.size_in_bytes()
        if self.vertMatls:
            size += HEAD + self.vertMaterialsSize()
        if self.materialPass is not None:
            size += HEAD + self.materialPass.size_in_bytes()
        if self.aabbtree is not None:
            size += HEAD + self.aabbtree.size_in_bytes()
        return size

    def write(self, file):
        write_chunk_head(file, W3D_CHUNK_MESH,
                         self.size_in_bytes(), hasSubChunks=True)
        self.header.write(file)

        write_chunk_head(file, W3D_CHUNK_VERTICES, self.vertsSize())
        write_array(file, self.verts, write_vector)

        write_chunk_head(file, W3D_CHUNK_VERTEX_NORMALS, self.normalsSize())
        write_array(file, self.normals, write_vector)

        write_chunk_head(file, W3D_CHUNK_TRIANGLES, self.trisSize())
        for tri in self.triangles:
            tri.write(file)

        if self.vertInfs:
            write_chunk_head(file, W3D_CHUNK_VERTEX_INFLUENCES,
                             self.vertInfsSize())
            for inf in self.vertInfs:
                inf.write(file)

        if self.shaders:
            write_chunk_head(file, W3D_CHUNK_SHADERS, self.shadersSize())
            for shader in self.shaders:
                shader.write(file)

        if self.textures:
            write_chunk_head(file, W3D_CHUNK_TEXTURES,
                             self.texturesSize(), hasSubChunks=True)
            for texture in self.textures:
                texture.write(file)

        if self.shadeIds:
            write_chunk_head(
                file, W3D_CHUNK_VERTEX_SHADE_INDICES, self.shadeIdsSize())
            write_array(file, self.shadeIds, write_long)

        if self.shaderMaterials:
            write_chunk_head(file, W3D_CHUNK_SHADER_MATERIALS,
                             self.shaderMaterialsSize(), hasSubChunks=True)
            for shaderMat in self.shaderMaterials:
                shaderMat.write(file)

        if self.matInfo is not None:
            write_chunk_head(file, W3D_CHUNK_MATERIAL_INFO,
                             self.matInfo.size_in_bytes())
            self.matInfo.write(file)

        if self.vertMatls:
            write_chunk_head(file, W3D_CHUNK_VERTEX_MATERIALS,
                             self.vertMaterialsSize(), hasSubChunks=True)
            for vertMat in self.vertMatls:
                vertMat.write(file)

        if self.materialPass is not None:
            self.materialPass.write(file)

        if self.aabbtree is not None:
            self.aabbtree.write(file)


#######################################################################################
# Unsupported
#######################################################################################

# inside mesh
W3D_CHUNK_PRELIT_UNLIT = 0x00000023
W3D_CHUNK_PRELIT_VERTEX = 0x00000024
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS = 0x00000025
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE = 0x00000026

W3D_CHUNK_DEFORM = 0x00000058
W3D_CHUNK_PS2_SHADERS = 0x00000080

# inside w3d file
W3D_CHUNK_MORPH_ANIMATION = 0x000002C0
W3D_CHUNK_HMODEL = 0x00000300
W3D_CHUNK_LODMODEL = 0x00000400
W3D_CHUNK_COLLECTION = 0x00000420
W3D_CHUNK_POINTS = 0x00000440
W3D_CHUNK_LIGHT = 0x00000460
W3D_CHUNK_EMITTER = 0x00000500
W3D_CHUNK_AGGREGATE = 0x00000600
W3D_CHUNK_NULL_OBJECT = 0x00000750
W3D_CHUNK_LIGHTSCAPE = 0x00000800
W3D_CHUNK_DAZZLE = 0x00000900
W3D_CHUNK_SOUNDROBJ = 0x00000A00
