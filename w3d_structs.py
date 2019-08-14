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
    def read(file, as_float=False):
        return RGBA(r=ord(file.read(1)),
            g = ord(file.read(1)),
            b = ord(file.read(1)),
            a = ord(file.read(1)))

    @staticmethod
    def read_f(file):
        return RGBA(r=read_float(file),
            g = read_float(file),
            b = read_float(file),
            a = read_float(file))


class Version(Struct):
    major = 5
    minor = 0

    @staticmethod
    def read(file):
        data = read_long(file)
        return Version(major=data >> 16,
            minor = data & 0xFFFF)


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
    header = HierarchyHeader()
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
                while file.tell() < subChunkEnd:
                    result.pivots.append(HierarchyPivot.read(file))
            elif chunkType == W3D_CHUNK_PIVOT_FIXUPS:
                while file.tell() < subChunkEnd:
                    result.pivot_fixups.append(read_vector(file))
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
            while file.tell() < chunkEnd:
                result.data.append(read_float(file))
        elif result.vectorLen == 4:
            while file.tell() < chunkEnd:
                result.data.append(read_quaternion(file))

        return result


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
                result.channels.append(AnimationChannel.read(file, subChunkEnd))
            else:
                skip_unknown_chunk(self, file, chunkType, chunkSize)

        return result

W3D_CHUNK_COMPRESSED_ANIMATION_HEADER = 0x00000281

#######################################################################################
# Compressed Animation
#######################################################################################

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
            result.timeCodes.append(
                TimeCodedDatum.read(file, result.type))

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

        file.read(3) # read unknown bytes at the end
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
            vectorIndex = vecIndex,
            blockIndex = read_unsigned_byte(file),
            deltaBytes = [])
    
        for _ in range(bits * 2):
            result.deltaBytes.append(read_signed_byte(file))
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
            bitCount = bits)

        count = (channel.numTimeCodes + 15) >> 4

        for _ in range(count):
            for j in range(channel.vectorLen):
                result.deltaBlocks.append(AdaptiveDeltaBlock.read(file, j, bits))

        return result


class TimeCodedBitChannel(Struct):
    #TODO
    data = 0


class MotionChannel(Struct):
    deltaType = 0
    vectorLen = 0
    type = 0
    numTimeCodes = 0
    pivot = 0
    data = []

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
            result.data = AdaptiveDeltaMotionAnimationChannel.read(file, result, 4)
        elif result.deltaType == 2:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(file, result, 8)
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
                    result.adaptiveDeltaChannels.append(AdaptiveDeltaAnimationChannel.read(file))
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


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703


class HLodArrayHeader(Struct):
    modelCount = 0
    maxScreenSize = 0.0


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    boneIndex = 0
    name = ""


W3D_CHUNK_HLOD_LOD_ARRAY = 0x00000702


class HLodArray(Struct):
    header = HLodArrayHeader()
    subObjects = []


W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = HLodHeader()
    lodArray = HLodArray()

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

#######################################################################################
# Texture
#######################################################################################


W3D_CHUNK_TEXTURE_INFO = 0x00000033


class TextureInfo(Struct):
    attributes = 0
    animationType = 0
    frameCount = 0
    frameRate = 0.0


W3D_CHUNK_TEXTURES = 0x00000030
W3D_CHUNK_TEXTURE = 0x00000031
W3D_CHUNK_TEXTURE_NAME = 0x00000032


class Texture(Struct):
    name = ""
    textureInfo = TextureInfo()

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


W3D_CHUNK_MATERIAL_INFO = 0x00000028


class MaterialInfo(Struct):
    passCount = 1
    vertMatlCount = 0
    shaderCount = 0
    textureCount = 0

#######################################################################################
# Vertices
#######################################################################################


class MeshVertexInfluence(Struct):
    boneIdx = 0
    xtraIdx = 0
    boneInf = 0.0
    xtraInf = 0.0

#######################################################################################
# Triangle
#######################################################################################


class MeshTriangle(Struct):
    vertIds = []
    attrs = 13 
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0

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

#######################################################################################
# Shader Material
#######################################################################################


W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52


class ShaderMaterialHeader(Struct):
    number = 0
    typeName = ""
    reserved = 0


W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x53


class ShaderMaterialProperty(Struct):
    type = 0
    name = ""
    value = None


W3D_CHUNK_SHADER_MATERIAL = 0x51


class ShaderMaterial(Struct):
    header = ShaderMaterialHeader()
    properties = []

#######################################################################################
# AABBTree (Axis-aligned-bounding-box)
#######################################################################################


W3D_CHUNK_AABBTREE_HEADER = 0x00000091


class AABBTreeHeader(Struct):
    nodeCount = 0
    polyCount = 0


class AABBTreeNode(Struct):
    min = Vector((0.0, 0.0, 0.0))
    max = Vector((0.0, 0.0, 0.0))
    frontOrPoly0 = 0
    backOrPolyCount = 0


W3D_CHUNK_AABBTREE = 0x00000090
W3D_CHUNK_AABBTREE_POLYINDICES = 0x00000092
W3D_CHUNK_AABBTREE_NODES = 0x00000093


class MeshAABBTree(Struct):
    header = AABBTreeHeader()
    polyIndices = []
    nodes = []

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
