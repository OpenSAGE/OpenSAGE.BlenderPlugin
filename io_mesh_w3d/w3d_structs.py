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


class Version(Struct):
    major = 5
    minor = 0

    @staticmethod
    def read(file):
        data = read_long(file)
        return Version(major=data >> 16,
                       minor=data & 0xFFFF)


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
            position=read_vector(file),
            eulerAngles=read_vector(file),
            rotation=read_quaternion(file))


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


W3D_CHUNK_ANIMATION = 0x00000200


class Animation(Struct):
    header = None
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


def format(val):
    str = "%.6f" % val
    return str.replace(".", ",") + "; "


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
    # TODO
    data = 0


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
    header = None
    timeCodedChannels = []
    adaptiveDeltaChannels = []
    timeCodedBitChannels = []
    motionChannels = []

    @staticmethod
    def read(self, file, chunkEnd):
        print("\n### NEW COMPRESSED ANIMATION: ###")
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
            # elif chunkType == W3D_CHUNK_COMPRESSED_BIT_CHANNEL:
            #    result.timeCodedBitChannels.append(read_time_coded_bit_channel(file))
            elif chunkType == W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL:
                result.motionChannels.append(
                    MotionChannel.read(file, subChunkEnd))
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)

        print("finished animation")
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


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703


class HLodArrayHeader(Struct):
    modelCount = 0
    maxScreenSize = 0.0

    @staticmethod
    def read(file):
        return HLodArrayHeader(
            modelCount=read_long(file),
            maxScreenSize=read_float(file))


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    boneIndex = 0
    name = ""

    @staticmethod
    def read(file):
        return HLodSubObject(
            boneIndex=read_long(file),
            name=read_long_fixed_string(file))


W3D_CHUNK_HLOD_LOD_ARRAY = 0x00000702


class HLodArray(Struct):
    header = None
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


W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = None
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
        # print("\n### NEW BOX: ###")
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


W3D_CHUNK_TEXTURES = 0x00000030
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


#######################################################################################
# Material
#######################################################################################


W3D_CHUNK_TEXTURE_STAGE = 0x00000048
W3D_CHUNK_TEXTURE_IDS = 0x00000049
W3D_CHUNK_STAGE_TEXCOORDS = 0x0000004A
W3D_CHUNK_PER_FACE_TEXCOORD_IDS = 0x0000004B


class MeshTextureStage(Struct):
    txIds = []
    perFaceTxCoords = []
    txCoords = []

    @staticmethod
    def read(self, file, chunkEnd):
        result = MeshTextureStage(
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


W3D_CHUNK_MATERIAL_PASS = 0x00000038
W3D_CHUNK_VERTEX_MATERIAL_IDS = 0x00000039
W3D_CHUNK_SHADER_IDS = 0x0000003A
W3D_CHUNK_DCG = 0x0000003B
W3D_CHUNK_DIG = 0x0000003C
W3D_CHUNK_SCG = 0x0000003E
W3D_CHUNK_SHADER_MATERIAL_ID = 0x3F


class MeshMaterialPass(Struct):
    vmIds = []
    shaderIds = []
    dcg = []
    dig = []
    scg = []
    shaderMaterialIds = []
    txStages = []
    txCoords = []

    @staticmethod
    def read(self, file, chunkEnd):
        result = MeshMaterialPass(
            vmIds=[],
            shaderIds=[],
             dcg=[],
            dig=[],
            scg=[],
            vertexMaterialIds=[],
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
                result.shaderMatIds = read_array(file, subChunkEnd, read_long)
            elif chunkType == W3D_CHUNK_TEXTURE_STAGE:
                result.txStages.append(
                    MeshTextureStage.read(self, file, subChunkEnd))
            elif chunkType == W3D_CHUNK_STAGE_TEXCOORDS:
                result.txCoords = read_array(file, subChunkEnd, read_vector2)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)

        return result


W3D_CHUNK_VERTEX_MATERIAL_INFO = 0x0000002D


class VertexMaterial(Struct):
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
        return VertexMaterial(
            attributes=read_long(file),
            ambient=RGBA.read(file),
            diffuse=RGBA.read(file),
            specular=RGBA.read(file),
            emissive=RGBA.read(file),
            shininess=read_float(file),
            opacity=read_float(file),
            translucency=read_float(file))


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


W3D_CHUNK_VERTEX_MATERIALS = 0x0000002A
W3D_CHUNK_VERTEX_MATERIAL = 0x0000002B
W3D_CHUNK_VERTEX_MATERIAL_NAME = 0x0000002C
W3D_CHUNK_VERTEX_MAPPER_ARGS0 = 0x0000002E
W3D_CHUNK_VERTEX_MAPPER_ARGS1 = 0x0000002F


class MeshMaterial(Struct):
    vmName = ""
    vmInfo = VertexMaterial()
    vmArgs0 = ""
    vmArgs1 = ""

    @staticmethod
    def read(self, file, chunkEnd):
        result = MeshMaterial()

        while file.tell() < chunkEnd:
            chunkType = read_long(file)
            chunkSize = get_chunk_size(read_long(file))

            if chunkType == W3D_CHUNK_VERTEX_MATERIAL_NAME:
                result.vmName = read_string(file)
            elif chunkType == W3D_CHUNK_VERTEX_MATERIAL_INFO:
                result.vmInfo = VertexMaterial.read(file)
            elif chunkType == W3D_CHUNK_VERTEX_MAPPER_ARGS0:
                result.vmArgs0 = read_string(file)
            elif chunkType == W3D_CHUNK_VERTEX_MAPPER_ARGS1:
                result.vmArgs1 = read_string(file)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)

        return result


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

#######################################################################################
# Shader
#######################################################################################


W3D_CHUNK_SHADERS = 0x00000029


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


W3D_CHUNK_SHADER_MATERIAL = 0x51


class ShaderMaterial(Struct):
    header = None
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


W3D_CHUNK_MESH = 0x00000000
W3D_CHUNK_VERTICES = 0x00000002
W3D_CHUNK_VERTICES_2 = 0xC00
W3D_CHUNK_VERTEX_NORMALS = 0x00000003
W3D_CHUNK_NORMALS_2 = 0xC01
W3D_CHUNK_MESH_USER_TEXT = 0x0000000C
W3D_CHUNK_VERTEX_INFLUENCES = 0x0000000E
W3D_CHUNK_TRIANGLES = 0x00000020
W3D_CHUNK_VERTEX_SHADE_INDICES = 0x00000022
W3D_CHUNK_SHADER_MATERIALS = 0x50
W3D_CHUNK_TANGENTS = 0x60
W3D_CHUNK_BITANGENTS = 0x61


class Mesh(Struct):
    header = MeshHeader()
    userText = ""
    verts = []
    verts_2 = []
    normals = []
    normals_2 = []
    vertInfs = []
    triangles = []
    tangents = []
    bitangents = []
    shadeIds = []
    matInfo = MaterialInfo()
    shaders = []
    vertMatls = []
    textures = []
    shaderMaterials = []
    materialPass = MeshMaterialPass()
    aabbtree = MeshAABBTree()

    @staticmethod
    def read(self, file, chunkEnd):
        result = Mesh(
            verts=[],
            verts_2=[],
            normals=[],
            normals_2=[],
            vertInfs=[],
            triangles=[],
            tangents=[],
            bitangents=[],
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
                result.verts_2 = read_array(file, subChunkEnd, read_vector)
            elif chunkType == W3D_CHUNK_VERTEX_NORMALS:
                result.normals = read_array(file, subChunkEnd, read_vector)
            elif chunkType == W3D_CHUNK_NORMALS_2:
                result.normals_2 = read_array(file, subChunkEnd, read_vector)
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
                    self, file, subChunkEnd, W3D_CHUNK_VERTEX_MATERIAL, MeshMaterial.read)
            elif chunkType == W3D_CHUNK_TEXTURES:
                result.textures = read_chunk_array(
                    self, file, subChunkEnd, W3D_CHUNK_TEXTURE, Texture.read)
            elif chunkType == W3D_CHUNK_MATERIAL_PASS:
                result.materialPass = MeshMaterialPass.read(
                    self, file, subChunkEnd)
            elif chunkType == W3D_CHUNK_SHADER_MATERIALS:
                result.shaderMaterials = read_chunk_array(
                    self, file, subChunkEnd, W3D_CHUNK_SHADER_MATERIAL, ShaderMaterial.read)
            elif chunkType == W3D_CHUNK_TANGENTS:
                result.tangents = read_array(file, subChunkEnd, read_vector)
            elif chunkType == W3D_CHUNK_BITANGENTS:
                result.bitangents == read_array(file, subChunkEnd, read_vector)
            elif chunkType == W3D_CHUNK_AABBTREE:
                result.aabbtree = MeshAABBTree.read(self, file, subChunkEnd)
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)

        return result
