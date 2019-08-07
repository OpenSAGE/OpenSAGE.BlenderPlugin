# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

from mathutils import Vector, Quaternion

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


class Version(Struct):
    major = 5
    minor = 0

#######################################################################################
# Hierarchy
#######################################################################################


W3D_CHUNK_HIERARCHY_HEADER = 0x00000101


class HierarchyHeader(Struct):
    version = Version()
    name = ""
    numPivots = 0
    center = Vector((0.0, 0.0, 0.0))


W3D_CHUNK_PIVOTS = 0x00000102


class HierarchyPivot(Struct):
    name = ""
    parentIdx = -1
    translation = Vector((0.0, 0.0, 0.0))
    eulerAngles = Vector((0.0, 0.0, 0.0))
    rotation = Quaternion((1.0, 0.0, 0.0, 0.0))


W3D_CHUNK_HIERARCHY = 0x00000100
W3D_CHUNK_PIVOT_FIXUPS = 0x00000103


class Hierarchy(Struct):
    header = HierarchyHeader()
    pivots = []
    pivot_fixups = []

#######################################################################################
# Animation
#######################################################################################


W3D_CHUNK_ANIMATION_HEADER = 0x00000201


class AnimationHeader(Struct):
    version = Version()
    name = ""
    hieraName = ""
    numFrames = 0
    frameRate = 0


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel(Struct):
    firstFrame = 0
    lastFrame = 0
    vectorLen = 0
    type = 0
    pivot = 0
    padding = 0
    data = []


W3D_CHUNK_ANIMATION = 0x00000200


class Animation(Struct):
    header = AnimationHeader()
    channels = []


W3D_CHUNK_COMPRESSED_ANIMATION_HEADER = 0x00000281


class CompressedAnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchyName = ""
    numFrames = 0
    frameRate = 0
    flavor = 0


class TimeCodedAnimationChannel(Struct):
    numTimeCodes = 0
    pivot = -1
    vectorLen = 0
    type = 0
    data = []


class AdaptiveDeltaAnimationChannel(Struct):
    numTimeCodes = 0
    pivot = -1
    vectorLen = 0
    type = 0
    scale = 0.0
    initialValue = None
    data = []


class TimeCodedBitChannel(Struct):
    data = 0


class MotionChannel(Struct):
    data = 0


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


class MeshTextureStage(Struct):
    txIds = []
    txCoords = []


class MeshMaterialPass(Struct):
    vmIds = []
    shaderIds = []
    dcg = []
    txStage = MeshTextureStage()  # has to be an array


class VertexMaterial(Struct):
    attributes = 0
    ambient = RGBA()  # alpha is only padding in this and below
    diffuse = RGBA()
    specular = RGBA()
    emissive = RGBA()
    # how tight the specular highlight will be, 1 - 1000 (default = 1) -float
    shininess = 0.0
    # how opaque the material is, 0.0 = invisible, 1.0 = fully opaque (default = 1) -float
    opacity = 0.0
    # how much light passes through the material. (default = 0) -float
    translucency = 0.0


class MeshMaterial(Struct):
    vmName = ""
    vmInfo = VertexMaterial()
    vmArgs0 = ""  # mapping / animation type of the texture
    vmArgs1 = ""  # mapping / animation type of the texture


W3D_CHUNK_MATERIAL_INFO = 0x00000028


class MaterialInfo(Struct):
    passCount = 1  # always 1
    vertMatlCount = 0
    shaderCount = 0
    textureCount = 0

#######################################################################################
# Vertices
#######################################################################################


class MeshVertexInfluences(Struct):
    boneIdx = 0
    xtraIdx = 0
    boneInf = 0.0
    xtraInf = 0.0

#######################################################################################
# Triangle
#######################################################################################


class MeshTriangle(Struct):
    vertIds = []
    attrs = 13  # SURFACE_TYPE_DEFAULT
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0  # distance from the face to the mesh center

#######################################################################################
# Shader
#######################################################################################


class MeshShader(Struct):
    #filled with some standard values
    depthCompare = 3
    depthMask = 1
    colorMask = 0
    destBlend = 0  # glBlendFunc  (GL_ZERO, GL_ONE, ...)
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
# Normal Map
#######################################################################################


class MeshNormalMapHeader(Struct):
    number = 0
    typeName = ""
    reserved = 0


class MeshNormalMapEntryStruct(Struct):
    unknown = 0  # dont know what this is for and what it is called
    diffuseTexName = ""
    unknown_nrm = 0  # dont know what this is for and what it is called
    normalMap = ""
    bumpScale = 0
    ambientColor = [0.0, 0.0, 0.0, 0.0]
    diffuseColor = [0.0, 0.0, 0.0, 0.0]
    specularColor = [0.0, 0.0, 0.0, 0.0]
    specularExponent = 0.0
    alphaTestEnable = 0


class MeshNormalMap(Struct):
    header = MeshNormalMapHeader()
    entryStruct = MeshNormalMapEntryStruct()


class MeshBumpMapArray(Struct):
    normalMap = MeshNormalMap()

#######################################################################################
# AABBTree (Axis-aligned-bounding-box)
#######################################################################################


class AABBTreeHeader(Struct):
    nodeCount = 0
    polyCount = 0


class AABBTreeNode(Struct):
    min = Vector((0.0, 0.0, 0.0))
    max = Vector((0.0, 0.0, 0.0))
    frontOrPoly0 = 0
    backOrPolyCount = 0


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


class Mesh(Struct):
    header = MeshHeader()
    verts = []
    verts_2 = []
    normals = []
    normals_2 = []
    vertInfs = []
    triangles = []
    userText = ""
    shadeIds = []
    matInfo = MaterialInfo()
    shaders = []
    vertMatls = []
    textures = []
    materialPass = MeshMaterialPass()
    bumpMaps = MeshBumpMapArray()
    aabbtree = MeshAABBTree()
