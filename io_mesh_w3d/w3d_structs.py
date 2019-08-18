# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

from mathutils import Vector, Quaternion
from io_mesh_w3d.w3d_io_binary import *
from io_mesh_w3d.utils_w3d import *
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


HEAD = 8  # 4(long = chunktype) + 4 (long = chunksize)

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
        data = read_long(file)
        return Version(major=data >> 16,
                       minor=data & 0xFFFF)

    def write(self, file):
        write_long(file, (self.major << 16) | self.minor)


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
            numPivots=read_long(file),
            centerPos=read_vector(file))

    def sizeInBytes(self):
        return 36

    def write(self, file):
        write_head(file, W3D_CHUNK_HIERARCHY_HEADER, self.sizeInBytes())
        self.version.write(file)
        write_fixed_string(file, self.name)
        write_long(file, self.numPivots)
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

    def sizeInBytes(self):
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
    header = None
    pivots = []
    pivot_fixups = []

    @staticmethod
    def read(self, file, chunkEnd):
        result = Hierarchy(
            pivots=[],
            pivot_fixups=[]
        )

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_HIERARCHY_HEADER:
                result.header = HierarchyHeader.read(file)
            elif chunkType == W3D_CHUNK_PIVOTS:
                result.pivots = read_array(
                    file, subChunkEnd, HierarchyPivot.read)
            elif chunkType == W3D_CHUNK_PIVOT_FIXUPS:
                result.pivot_fixups = read_array(
                    file, subChunkEnd, read_vector)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def pivotsSize(self):
        size = 0
        for pivot in self.pivots:
            size += pivot.sizeInBytes()
        return size

    def pivotFixupsSize(self):
        size = 0
        for _ in self.pivot_fixups:
            size += 12  # size in bytes
        return size

    def sizeInBytes(self):
        size = HEAD + self.header.sizeInBytes()
        size += HEAD + self.pivotsSize()
        if (len(self.pivot_fixups) > 0):
            size += HEAD + self.pivotFixupsSize()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_HIERARCHY, self.sizeInBytes())
        self.header.write(file)
        write_long(file, W3D_CHUNK_PIVOTS)
        write_long(file, self.pivotsSize())
        for pivot in self.pivots:
            pivot.write(file)

        if (len(self.pivot_fixups) > 0):
            write_long(file, W3D_CHUNK_PIVOT_FIXUPS)
            write_long(file, self.pivotFixupsSize())
            for fixup in self.pivot_fixups:
                write_vector(file, fixup)


#######################################################################################
# Animation
#######################################################################################


W3D_CHUNK_ANIMATION_HEADER = 0x00000201


class AnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchyName = ""
    numFrames = 0
    frameRate = 0

    @staticmethod
    def read(file):
        return AnimationHeader(
            version=Version.read(file),
            name=read_fixed_string(file),
            hierarchyName=read_fixed_string(file),
            numFrames=read_long(file),
            frameRate=read_long(file))

    def sizeInBytes(self):
        return 44

    def write(self, file):
        write_head(file, W3D_CHUNK_ANIMATION_HEADER, self.sizeInBytes())
        self.version.write(file)
        write_fixed_string(file, self.name)
        write_fixed_string(file, self.hierarchyName)
        write_long(file, self.numFrames)
        write_long(file, self.frameRate)


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel(Struct):
    firstFrame = 0
    lastFrame = 0
    vectorLen = 0
    type = 0
    pivot = 0
    padding = 0
    data = []

    @staticmethod
    def read(file, chunkEnd):
        result = AnimationChannel(
            firstFrame=read_short(file),
            lastFrame=read_short(file),
            vectorLen=read_short(file),
            type=read_short(file),
            pivot=read_short(file),
            padding=read_short(file),
            data=[])

        if result.vectorLen == 1:
            result.data = read_array(file, chunkEnd, read_float)
        elif result.vectorLen == 4:
            result.data = read_array(file, chunkEnd, read_quaternion)
        return result

    def sizeInBytes(self):
        return 12 + (len(self.data) * self.vectorLen) * 4

    def write(self, file):
        write_head(file, W3D_CHUNK_ANIMATION_CHANNEL, self.sizeInBytes())

        write_short(file, self.firstFrame)
        write_short(file, self.lastFrame)
        write_short(file, self.vectorLen)
        write_short(file, self.type)
        write_short(file, self.pivot)
        write_short(file, self.padding)

        for d in self.data:
            if (self.vectorLen == 1):
                write_float(file, d)
            else:
                write_quaternion(file, d)


W3D_CHUNK_ANIMATION = 0x00000200


class Animation(Struct):
    header = AnimationHeader()
    channels = []

    @staticmethod
    def read(self, file, chunkEnd):
        result = Animation(channels=[])

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_ANIMATION_HEADER:
                result.header = AnimationHeader.read(file)
            elif chunkType == W3D_CHUNK_ANIMATION_CHANNEL:
                result.channels.append(
                    AnimationChannel.read(file, subChunkEnd))
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def sizeInBytes(self):
        size = HEAD + self.header.sizeInBytes()
        for channel in self.channels:
            size += HEAD + channel.sizeInBytes()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_ANIMATION,
                   self.sizeInBytes(), hasSubChunks=True)
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
    hierarchyName = ""
    numFrames = 0
    frameRate = 0
    flavor = 0

    @staticmethod
    def read(file):
        return CompressedAnimationHeader(
            version=Version.read(file),
            name=read_fixed_string(file),
            hierarchyName=read_fixed_string(file),
            numFrames=read_long(file),
            frameRate=read_short(file),
            flavor=read_short(file))


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
            numTimeCodes=read_long(file),
            pivot=read_short(file),
            vectorLen=read_unsigned_byte(file),
            type=read_unsigned_byte(file),
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
            numTimeCodes=read_long(file),
            pivot=read_short(file),
            vectorLen=read_unsigned_byte(file),
            type=read_unsigned_byte(file),
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
            blockIndex=read_unsigned_byte(file),
            deltaBytes=[])

        result.deltaBytes = read_fixed_array(file, bits * 2, read_signed_byte)
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
            type=read_unsigned_byte(file),
            defaultValue=read_unsigned_byte(file),
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

        if (not channel.numTimeCodes % 2 == 0):
            read_short(file)  # alignment

        for x in range(channel.numTimeCodes):
            result[x].value = read_channel_value(file, channel.type)
        return result

    @staticmethod
    def read(file, chunkEnd):
        read_unsigned_byte(file)  # zero

        result = MotionChannel(
            deltaType=read_unsigned_byte(file),
            vectorLen=read_unsigned_byte(file),
            type=read_unsigned_byte(file),
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
    def read(self, file, chunkEnd):
        result = CompressedAnimation(
            timeCodedChannels=[],
            adaptiveDeltaChannels=[],
            timeCodedBitChannels=[],
            motionChannels=[])

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_COMPRESSED_ANIMATION_HEADER:
                result.header = CompressedAnimationHeader.read(file)
            elif chunkType == W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL:
                if result.header.flavor == 0:
                    result.timeCodedChannels.append(
                        TimeCodedAnimationChannel.read(file))
                elif result.header.flavor == 1:
                    result.adaptiveDeltaChannels.append(
                        AdaptiveDeltaAnimationChannel.read(file))
                else:
                    skip_unknown_chunk(self, file, chunkType, chunkSize)
            elif chunkType == W3D_CHUNK_COMPRESSED_BIT_CHANNEL:
                result.timeCodedBitChannels.append(
                    TimeCodedBitChannel.read(file))
            elif chunkType == W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL:
                result.motionChannels.append(
                    MotionChannel.read(file, subChunkEnd))
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

#######################################################################################
# HLod
#######################################################################################


W3D_CHUNK_HLOD_HEADER = 0x00000701


class HLodHeader(Struct):
    version = Version()
    lodCount = 1
    modelName = ""
    hierarchyName = ""

    @staticmethod
    def read(file):
        return HLodHeader(
            version=Version.read(file),
            lodCount=read_long(file),
            modelName=read_fixed_string(file),
            hierarchyName=read_fixed_string(file))

    def sizeInBytes(self):
        return 40

    def write(self, file):
        write_head(file, W3D_CHUNK_HLOD_HEADER, self.sizeInBytes())
        self.version.write(file)
        write_long(file, self.lodCount)
        write_fixed_string(file, self.modelName)
        write_fixed_string(file, self.hierarchyName)


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703


class HLodArrayHeader(Struct):
    modelCount = 0
    maxScreenSize = 0.0

    @staticmethod
    def read(file):
        return HLodArrayHeader(
            modelCount=read_long(file),
            maxScreenSize=read_float(file))

    def sizeInBytes(self):
        return HEAD

    def write(self, file):
        write_head(file, W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER,
                   self.sizeInBytes())
        write_long(file, self.modelCount)
        write_float(file, self.maxScreenSize)


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    boneIndex = 0
    name = ""

    @staticmethod
    def read(file):
        return HLodSubObject(
            boneIndex=read_long(file),
            name=read_long_fixed_string(file))

    def sizeInBytes(self):
        return 36

    def write(self, file):
        write_head(file, W3D_CHUNK_HLOD_SUB_OBJECT, self.sizeInBytes())
        write_long(file, self.boneIndex)
        write_long_fixed_string(file, self.name)


W3D_CHUNK_HLOD_LOD_ARRAY = 0x00000702


class HLodArray(Struct):
    header = HLodHeader()
    subObjects = []

    @staticmethod
    def read(self, file, chunkEnd):
        result = HLodArray(
            header=None,
            subObjects=[])

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))

            if chunkType == W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER:
                result.header = HLodArrayHeader.read(file)
            elif chunkType == W3D_CHUNK_HLOD_SUB_OBJECT:
                result.subObjects.append(HLodSubObject.read(file))
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def sizeInBytes(self):
        size = HEAD + self.header.sizeInBytes()
        for obj in self.subObjects:
            size += HEAD + obj.sizeInBytes()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_HLOD_LOD_ARRAY,
                   self.sizeInBytes(), hasSubChunks=True)
        self.header.write(file)
        for obj in self.subObjects:
            obj.write(file)


W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = HLodHeader()
    lodArray = None

    @staticmethod
    def read(self, file, chunkEnd):
        result = HLod(
            header=None,
            lodArray=None
        )

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_HLOD_HEADER:
                result.header = HLodHeader.read(file)
            elif chunkType == W3D_CHUNK_HLOD_LOD_ARRAY:
                result.lodArray = HLodArray.read(self, file, subChunkEnd)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def sizeInBytes(self):
        size = HEAD + self.header.sizeInBytes()
        size += HEAD + self.lodArray.sizeInBytes()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_HLOD, self.sizeInBytes(), hasSubChunks=True)
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
        ver = Version.read(file),
        flags = read_long(file)
        return Box(
            version=ver,
            boxType=(flags & 0b11),
            collisionTypes=(flags & 0xFF0),
            name=read_long_fixed_string(file),
            color=RGBA.read(file),
            center=read_vector(file),
            extend=read_vector(file))

    def sizeInBytes(self):
        return 68

    def write(self, file):
        write_head(file, W3D_CHUNK_BOX, self.sizeInBytes())

        # TODO: fix version writing
        # self.version.write(file)
        write_long(file, 9)

        write_long(file, (self.collisionTypes & 0xFF) | (self.boxType & 0b11))
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
    frameRate = 0.0

    @staticmethod
    def read(file):
        return TextureInfo(
            attributes=read_short(file),
            animationType=read_short(file),
            frameCount=read_long(file),
            frameRate=read_float(file))

    def sizeInBytes(self):
        return 12

    def write(self, file):
        write_head(file, W3D_CHUNK_TEXTURE_INFO, self.sizeInBytes())
        write_short(file, self.attributes)
        write_short(file, self.animationType)
        write_long(file, self.frameCount)
        write_float(file, self.frameRate)


W3D_CHUNK_TEXTURE = 0x00000031
W3D_CHUNK_TEXTURE_NAME = 0x00000032


class Texture(Struct):
    name = ""
    textureInfo = None

    @staticmethod
    def read(self, file, chunkEnd):
        result = Texture(textureInfo=None)

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))

            if chunkType == W3D_CHUNK_TEXTURE_NAME:
                result.name = read_string(file)
            elif chunkType == W3D_CHUNK_TEXTURE_INFO:
                result.textureInfo = TextureInfo.read(file)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def sizeInBytes(self):
        size = HEAD + string_size(self.name)
        if self.textureInfo != None:
            size += HEAD + self.textureInfo.sizeInBytes()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_TEXTURE,
                   self.sizeInBytes(), hasSubChunks=True)
        write_head(file, W3D_CHUNK_TEXTURE_NAME, string_size(self.name))
        write_string(file, self.name)

        if self.textureInfo != None:
            write_head(file, W3D_CHUNK_TEXTURE_INFO, self.textureInfo.sizeInBytes())
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
    def read(self, file, chunkEnd):
        result = TextureStage(
            txIds=[],
            perFaceTxCoords=[],
            txCoords=[])

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_TEXTURE_IDS:
                result.txIds = read_array(file, subChunkEnd, read_long)
            elif chunkType == W3D_CHUNK_STAGE_TEXCOORDS:
                result.txCoords = read_array(file, subChunkEnd, read_vector2)
            elif chunkType == W3D_CHUNK_PER_FACE_TEXCOORD_IDS:
                result.perFaceTxCoords = read_array(
                    file, subChunkEnd, read_vector)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def txIdsSize(self):
        return len(self.txIds) * 4

    def perFaceTxCoordsSize(self):
        return len(self.perFaceTxCoords) * 12

    def txCoordsSize(self):
        return len(self.txCoords) * 8

    def sizeInBytes(self):
        size = 0
        if len(self.txIds) > 0:
            size += HEAD + self.txIdsSize()
        if len(self.txCoords) > 0:
            size += HEAD + self.txCoordsSize()
        if len(self.perFaceTxCoords) > 0:
            size += HEAD + self.perFaceTxCoordsSize()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_TEXTURE_STAGE,
                   self.sizeInBytes(), hasSubChunks=True)

        if len(self.txIds) > 0:
            write_head(file, W3D_CHUNK_TEXTURE_IDS, self.txIdsSize())
            write_array(file, self.txIds, write_long)

        if len(self.txCoords) > 0:
            write_head(file, W3D_CHUNK_STAGE_TEXCOORDS, self.txCoordsSize())
            write_array(file, self.txCoords, write_vector2)

        if len(self.perFaceTxCoords) > 0:
            write_head(file, W3D_CHUNK_PER_FACE_TEXCOORD_IDS,
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
    def read(self, file, chunkEnd):
        result = MaterialPass(
            vertexMaterialIds=[],
            shaderIds=[],
            dcg=[],
            dig=[],
            scg=[],
            shaderMaterialIds=[],
            txStages=[],
            txCoords=[])

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_VERTEX_MATERIAL_IDS:
                result.vertexMaterialIds = read_array(
                    file, subChunkEnd, read_long)
            elif chunkType == W3D_CHUNK_SHADER_IDS:
                result.shaderIds = read_array(file, subChunkEnd, read_long)
            elif chunkType == W3D_CHUNK_DCG:
                result.dcg = read_array(file, subChunkEnd, RGBA.read)
            elif chunkType == W3D_CHUNK_DIG:
                result.dig = read_array(file, subChunkEnd, RGBA.read)
            elif chunkType == W3D_CHUNK_SCG:
                result.scg = read_array(file, subChunkEnd, RGBA.read)
            elif chunkType == W3D_CHUNK_SHADER_MATERIAL_ID:
                result.shaderMaterialIds = read_array(file, subChunkEnd, read_long)
            elif chunkType == W3D_CHUNK_TEXTURE_STAGE:
                result.txStages.append(
                    TextureStage.read(self, file, subChunkEnd))
            elif chunkType == W3D_CHUNK_STAGE_TEXCOORDS:
                result.txCoords = read_array(file, subChunkEnd, read_vector2)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
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
            size += HEAD + stage.sizeInBytes()
        return size

    def txCoordsSize(self):
        return len(self.txCoords) * 8

    def sizeInBytes(self):
        size = 0
        if len(self.vertexMaterialIds) > 0:
            size = HEAD + self.vertexMaterialIdsSize()
        if len(self.shaderIds) > 0:
            size += HEAD + self.shaderIdsSize()
        if len(self.dcg) > 0:
            size += HEAD + self.dcgSize()
        if len(self.dig) > 0:
            size += HEAD + self.digSize()
        if len(self.scg) > 0:
            size += HEAD + self.scgSize()
        if len(self.shaderMaterialIds) > 0:
            size += HEAD + self.shaderMaterialIdsSize()
        if len(self.txStages) > 0:
            size += self.txStagesSize()
        if len(self.txCoords) > 0:
            size += HEAD + self.txCoordsSize()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_MATERIAL_PASS, self.sizeInBytes(), hasSubChunks=True)

        if len(self.vertexMaterialIds) > 0:
            write_head(file, W3D_CHUNK_VERTEX_MATERIAL_IDS, self.vertexMaterialIdsSize())
            write_array(file, self.vertexMaterialIds, write_long)
        if len(self.shaderIds) > 0:
            write_head(file, W3D_CHUNK_SHADER_IDS, self.shaderIdsSize())
            write_array(file, self.shaderIds, write_long)
        if len(self.dcg) > 0:
            write_head(file, W3D_CHUNK_DCG, self.dcgSize())
            for d in self.dcg:
                d.write(file)
        if len(self.dig) > 0:
            write_head(file, W3D_CHUNK_DIG, self.digSize())
            for d in self.dig:
                d.write(file)
        if len(self.scg) > 0:
            write_head(file, W3D_CHUNK_SCG, self.scgSize())
            for d in self.scg:
                d.write(file)
        if len(self.shaderMaterialIds) > 0:
            write_head(file, W3D_CHUNK_SHADER_MATERIAL_ID, self.shaderMaterialIdsSize())
            write_array(file, self.shaderMaterialIds, write_long)
        if len(self.txStages) > 0:
            for txStage in self.txStages:
                txStage.write(file)
        if len(self.txCoords) > 0:
            write_head(file, W3D_CHUNK_STAGE_TEXCOORDS, self.txCoordsSize())
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
            passCount=read_long(file),
            vertMatlCount=read_long(file),
            shaderCount=read_long(file),
            textureCount=read_long(file))

    def sizeInBytes(self):
        return 16

    def write(self, file):
        write_long(file, self.passCount)
        write_long(file, self.vertMatlCount)
        write_long(file, self.shaderCount)
        write_long(file, self.textureCount)


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

    def sizeInBytes(self):
        return 32

    def write(self, file):
        write_head(file, W3D_CHUNK_VERTEX_MATERIAL_INFO, self.sizeInBytes())
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
    def read(self, file, chunkEnd):
        result = VertexMaterial()

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))

            if chunkType == W3D_CHUNK_VERTEX_MATERIAL_NAME:
                result.vmName = read_string(file)
            elif chunkType == W3D_CHUNK_VERTEX_MATERIAL_INFO:
                result.vmInfo = VertexMaterialInfo.read(file)
            elif chunkType == W3D_CHUNK_VERTEX_MAPPER_ARGS0:
                result.vmArgs0 = read_string(file)
            elif chunkType == W3D_CHUNK_VERTEX_MAPPER_ARGS1:
                result.vmArgs1 = read_string(file)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def sizeInBytes(self):
        size = HEAD + string_size(self.vmName)
        size += HEAD + self.vmInfo.sizeInBytes()
        size += HEAD + string_size(self.vmArgs0)
        size += HEAD + string_size(self.vmArgs1)
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_VERTEX_MATERIAL, self.sizeInBytes(), hasSubChunks=True)
        write_head(file, W3D_CHUNK_VERTEX_MATERIAL_NAME, string_size(self.vmName))
        write_string(file, self.vmName)
        self.vmInfo.write(file)
        write_head(file, W3D_CHUNK_VERTEX_MAPPER_ARGS0, string_size(self.vmArgs0))
        write_string(file, self.vmArgs0)
        write_head(file, W3D_CHUNK_VERTEX_MAPPER_ARGS1, string_size(self.vmArgs1))
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
            boneIdx=read_short(file),
            xtraIdx=read_short(file),
            boneInf=read_short(file)/100,
            xtraInf=read_short(file)/100)

    def sizeInBytes(self):
        return 8

    def write(self, file):
        write_short(file, self.boneIdx)
        write_short(file, self.xtraIdx)
        write_short(file, int(self.boneInf * 100))
        write_short(file, int(self.xtraInf * 100))


#######################################################################################
# Triangle
#######################################################################################


class MeshTriangle(Struct):
    vertIds = []
    attrs = 13
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0

    @staticmethod
    def read(file):
        return MeshTriangle(
            vertIds=(read_long(file), read_long(file), read_long(file)),
            attrs=read_long(file),
            normal=read_vector(file),
            distance=read_float(file))

    def sizeInBytes(self):
        return 32

    def write(self, file):
        write_long(file, self.vertIds[0])
        write_long(file, self.vertIds[1])
        write_long(file, self.vertIds[2])
        write_long(file, self.attrs)
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
            depthCompare=read_unsigned_byte(file),
            depthMask=read_unsigned_byte(file),
            colorMask=read_unsigned_byte(file),
            destBlend=read_unsigned_byte(file),
            fogFunc=read_unsigned_byte(file),
            priGradient=read_unsigned_byte(file),
            secGradient=read_unsigned_byte(file),
            srcBlend=read_unsigned_byte(file),
            texturing=read_unsigned_byte(file),
            detailColorFunc=read_unsigned_byte(file),
            detailAlphaFunc=read_unsigned_byte(file),
            shaderPreset=read_unsigned_byte(file),
            alphaTest=read_unsigned_byte(file),
            postDetailColorFunc=read_unsigned_byte(file),
            postDetailAlphaFunc=read_unsigned_byte(file),
            pad=read_unsigned_byte(file))

    def sizeInBytes(self):
        return 16

    def write(self, file):
        write_unsigned_byte(file, self.depthCompare)
        write_unsigned_byte(file, self.depthMask)
        write_unsigned_byte(file, self.colorMask)
        write_unsigned_byte(file, self.destBlend)
        write_unsigned_byte(file, self.fogFunc)
        write_unsigned_byte(file, self.priGradient)
        write_unsigned_byte(file, self.secGradient)
        write_unsigned_byte(file, self.srcBlend)
        write_unsigned_byte(file, self.texturing)
        write_unsigned_byte(file, self.detailColorFunc)
        write_unsigned_byte(file, self.detailAlphaFunc)
        write_unsigned_byte(file, self.shaderPreset)
        write_unsigned_byte(file, self.alphaTest)
        write_unsigned_byte(file, self.postDetailColorFunc)
        write_unsigned_byte(file, self.postDetailAlphaFunc)
        write_unsigned_byte(file, self.pad)


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
            number=read_unsigned_byte(file),
            typeName=read_long_fixed_string(file),
            reserved=read_long(file))

    def sizeInBytes(self):
        return 37

    def write(self, file):
        write_head(file, W3D_CHUNK_SHADER_MATERIAL_HEADER, self.sizeInBytes())
        write_unsigned_byte(file, self.number)
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
            result.value = read_unsigned_byte(file)
        return result


    def sizeInBytes(self):
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
        write_head(file, W3D_CHUNK_SHADER_MATERIAL_PROPERTY, self.sizeInBytes())
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
            write_unsigned_byte(file, self.value)


W3D_CHUNK_SHADER_MATERIAL = 0x51


class ShaderMaterial(Struct):
    header = ShaderMaterialHeader()
    properties = []

    @staticmethod
    def read(self, file, chunkEnd):
        result = ShaderMaterial(
            properties=[])

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))

            if chunkType == W3D_CHUNK_SHADER_MATERIAL_HEADER:
                result.header = ShaderMaterialHeader.read(file)
            elif chunkType == W3D_CHUNK_SHADER_MATERIAL_PROPERTY:
                result.properties.append(ShaderMaterialProperty.read(file))
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def sizeInBytes(self):
        size = HEAD + self.header.sizeInBytes()
        for prop in self.properties:
            size += HEAD + prop.sizeInBytes()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_SHADER_MATERIAL, self.sizeInBytes(), hasSubChunks=True)
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
            nodeCount=read_long(file),
            poyCount=read_long(file))

        file.read(24)  # padding
        return result

    def sizeInBytes(self):
        return 8

    def write(self, file):
        write_head(file, W3D_CHUNK_AABBTREE_HEADER, self.sizeInBytes())
        write_long(file, self.nodeCount)
        write_long(file, self.polyCount)


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

    def sizeInBytes(self):
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
    def read(self, file, chunkEnd):
        result = MeshAABBTree()

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_AABBTREE_HEADER:
                result.header = AABBTreeHeader.read(file)
            elif chunkType == W3D_CHUNK_AABBTREE_POLYINDICES:
                result.polyIndices = read_array(file, subChunkEnd, read_long)
            elif chunkType == W3D_CHUNK_AABBTREE_NODES:
                result.nodes = read_array(file, subChunkEnd, AABBTreeNode.read)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def polyIndicesSize(self):
        return len(self.polyIndices) * 4

    def nodesSize(self):
        size = 0
        for node in self.nodes:
            size += node.sizeInBytes()
        return size

    def sizeInBytes(self):
        size = HEAD + self.header.sizeInBytes()
        if len(self.polyIndices) > 0:
            size += HEAD + self.polyIndicesSize()
        if len(self.nodes) > 0:
            size += HEAD + self.nodesSize()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_AABBTREE,
                   self.sizeInBytes(), hasSubChunks=True)
        self.header.write(file)

        if len(self.polyIndices) > 0:
            write_head(file, W3D_CHUNK_AABBTREE_POLYINDICES,
                       self.polyIndicesSize())
            write_array(file, self.polyIndices, write_long)
        if len(self.nodes) > 0:
            write_head(file, W3D_CHUNK_AABBTREE_NODES, self.nodesSize())
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
    vertChannelCount = 3
    faceChannelCount = 1
    minCorner = Vector((0.0, 0.0, 0.0))
    maxCorner = Vector((0.0, 0.0, 0.0))
    sphCenter = Vector((0.0, 0.0, 0.0))
    sphRadius = 0.0

    @staticmethod
    def read(file):
        return MeshHeader(
            version=Version.read(file),
            attrs=read_long(file),
            meshName=read_fixed_string(file),
            containerName=read_fixed_string(file),
            faceCount=read_long(file),
            vertCount=read_long(file),
            matlCount=read_long(file),
            damageStageCount=read_long(file),
            sortLevel=read_long(file),
            prelitVersion=read_long(file),
            futureCount=read_long(file),
            vertChannelCount=read_long(file),
            faceChannelCount=read_long(file),
            # bounding volumes
            minCorner=read_vector(file),
            maxCorner=read_vector(file),
            sphCenter=read_vector(file),
            sphRadius=read_float(file))

    def sizeInBytes(self):
        return 116

    def write(self, file):
        write_head(file, W3D_CHUNK_MESH_HEADER, self.sizeInBytes())
        self.version.write(file)
        write_long(file, self.attrs)
        write_fixed_string(file, self.meshName)
        write_fixed_string(file, self.containerName)
        write_long(file, self.faceCount)
        write_long(file, self.vertCount)
        write_long(file, self.matlCount)
        write_long(file, self.damageStageCount)
        write_long(file, self.sortLevel)
        write_long(file, self.prelitVersion)
        write_long(file, self.futureCount)
        write_long(file, self.vertChannelCount)
        write_long(file, self.faceChannelCount)
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

    @staticmethod
    def read(self, file, chunkEnd):
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

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))
            subChunkEnd = file.tell() + chunkSize

            if chunkType == W3D_CHUNK_VERTICES:
                result.verts = read_array(file, subChunkEnd, read_vector)
            elif chunkType == W3D_CHUNK_VERTICES_2:
                print("-> vertices 2 chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_VERTEX_NORMALS:
                result.normals = read_array(file, subChunkEnd, read_vector)
            elif chunkType == W3D_CHUNK_NORMALS_2:
                print("-> normals 2 chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_MESH_USER_TEXT:
                result.userText = read_string(file)
            elif chunkType == W3D_CHUNK_VERTEX_INFLUENCES:
                result.vertInfs = read_array(
                    file, subChunkEnd, MeshVertexInfluence.read)
            elif chunkType == W3D_CHUNK_MESH_HEADER:
                result.header = MeshHeader.read(file)
            elif chunkType == W3D_CHUNK_TRIANGLES:
                result.triangles = read_array(
                    file, subChunkEnd, MeshTriangle.read)
            elif chunkType == W3D_CHUNK_VERTEX_SHADE_INDICES:
                result.shadeIds = read_array(file, subChunkEnd, read_long)
            elif chunkType == W3D_CHUNK_MATERIAL_INFO:
                result.matInfo = MaterialInfo.read(file)
            elif chunkType == W3D_CHUNK_SHADERS:
                result.shaders = read_array(file, subChunkEnd, MeshShader.read)
            elif chunkType == W3D_CHUNK_VERTEX_MATERIALS:
                result.vertMatls = read_chunk_array(
                    self, file, subChunkEnd, W3D_CHUNK_VERTEX_MATERIAL, VertexMaterial.read)
            elif chunkType == W3D_CHUNK_TEXTURES:
                result.textures = read_chunk_array(
                    self, file, subChunkEnd, W3D_CHUNK_TEXTURE, Texture.read)
            elif chunkType == W3D_CHUNK_MATERIAL_PASS:
                result.materialPass = MaterialPass.read(
                    self, file, subChunkEnd)
            elif chunkType == W3D_CHUNK_SHADER_MATERIALS:
                result.shaderMaterials = read_chunk_array(
                    self, file, subChunkEnd, W3D_CHUNK_SHADER_MATERIAL, ShaderMaterial.read)
            elif chunkType == W3D_CHUNK_TANGENTS:
                print("-> tangents chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_BITANGENTS:
                print("-> bitangents chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_AABBTREE:
                result.aabbtree = MeshAABBTree.read(self, file, subChunkEnd)
            elif chunkType == W3D_CHUNK_PRELIT_UNLIT:
                print("-> prelit unlit chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_PRELIT_VERTEX:
                print("-> prelit vertex chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS:
                print("-> prelit lightmap multi pass chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE:
                print("-> prelit lightmap multi texture chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_DEFORM:
                print("-> deform chunk is not supported")
                file.seek(chunkSize, 1)
            elif chunkType == W3D_CHUNK_PS2_SHADERS:
                print("-> ps2 shaders chunk is not supported")
                file.seek(chunkSize, 1)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)
        return result

    def vertsSize(self):
        return len(self.verts) * 12

    def normalsSize(self):
        return len(self.normals) * 12

    def trisSize(self):
        size = 0
        for t in self.triangles:
            size += t.sizeInBytes()
        return size

    def vertInfsSize(self):
        size = 0
        for inf in self.vertInfs:
            size += inf.sizeInBytes()
        return size

    def shadersSize(self):
        size = 0
        for shader in self.shaders:
            size += shader.sizeInBytes()
        return size

    def texturesSize(self):
        size = 0
        for texture in self.textures:
            size += HEAD + texture.sizeInBytes()
        return size

    def shadeIdsSize(self):
        return len(self.shadeIds) * 4

    def shaderMaterialsSize(self):
        size = 0
        for shaderMat in self.shaderMaterials:
            size += HEAD + shaderMat.sizeInBytes()
        return size

    def vertMaterialsSize(self):
        size = 0
        for vertMat in self.vertMatls:
            size += HEAD + vertMat.sizeInBytes()
        return size

    def sizeInBytes(self):
        size = HEAD + self.header.sizeInBytes()
        size += HEAD + self.vertsSize()
        size += HEAD + self.normalsSize()
        size += HEAD + self.trisSize()
        if len(self.vertInfs) > 0:
            size += HEAD + self.vertInfsSize()
        if len(self.shaders) > 0:
            size += HEAD + self.shadersSize()
        if len(self.textures) > 0:
            size += HEAD + self.texturesSize()
        if len(self.shadeIds) > 0:
            size += HEAD + self.shadeIdsSize()
        if len(self.shaderMaterials) > 0:
            size += HEAD + self.shaderMaterialsSize()
        if self.matInfo != None:
            size += HEAD + self.matInfo.sizeInBytes()
        if len(self.vertMatls) > 0:
            size += HEAD + self.vertMaterialsSize()
        if self.materialPass != None:
            size += HEAD + self.materialPass.sizeInBytes()
        if self.aabbtree != None:
            size += HEAD + self.aabbtree.sizeInBytes()
        return size

    def write(self, file):
        write_head(file, W3D_CHUNK_MESH, self.sizeInBytes(), hasSubChunks=True)
        self.header.write(file)

        write_head(file, W3D_CHUNK_VERTICES, self.vertsSize())
        write_array(file, self.verts, write_vector)

        write_head(file, W3D_CHUNK_VERTEX_NORMALS, self.normalsSize())
        write_array(file, self.normals, write_vector)

        write_head(file, W3D_CHUNK_TRIANGLES, self.trisSize())
        for tri in self.triangles:
            tri.write(file)

        if len(self.vertInfs) > 0:
            write_head(file, W3D_CHUNK_VERTEX_INFLUENCES, self.vertInfsSize())
            for inf in self.vertInfs:
                inf.write(file)

        if len(self.shaders) > 0:
            write_head(file, W3D_CHUNK_SHADERS, self.shadersSize())
            for shader in self.shaders:
                shader.write(file)

        if len(self.textures) > 0:
            write_head(file, W3D_CHUNK_TEXTURES, self.texturesSize(), hasSubChunks=True)
            for texture in self.textures:
                texture.write(file)

        if len(self.shadeIds) > 0:
            write_head(file, W3D_CHUNK_VERTEX_SHADE_INDICES, self.shadeIdsSize())
            write_array(file, self.shadeIds, write_long)

        if len(self.shaderMaterials) > 0:
            write_head(file, W3D_CHUNK_SHADER_MATERIALS, self.shaderMaterialsSize(), hasSubChunks=True)
            for shaderMat in self.shaderMaterials:
                shaderMat.write(file)

        if self.matInfo != None:
            write_head(file, W3D_CHUNK_MATERIAL_INFO, self.matInfo.sizeInBytes())
            self.matInfo.write(file)

        if len(self.vertMatls) > 0:
            write_head(file, W3D_CHUNK_VERTEX_MATERIALS, self.vertMaterialsSize(), hasSubChunks=True)
            for vertMat in self.vertMatls:
                vertMat.write(file)

        if self.materialPass != None:
            self.materialPass.write(file)

        if self.aabbtree != None:
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
