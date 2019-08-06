import bpy
import os
import bmesh
from io_mesh_w3d.w3d_io_binary import *
from io_mesh_w3d.w3d_structs import *
from io_mesh_w3d.utils_w3d import *
    
#######################################################################################
# Hierarchy
#######################################################################################

def read_hierarchy_header(file):
    return HierarchyHeader(
        version = GetVersion(ReadLong(file)),
        name = ReadFixedString(file),
        pivotCount = ReadLong(file),
        centerPos = ReadVector(file))
        
def read_pivots(file, chunkEnd):
    pivots = []
    while file.tell() < chunkEnd:
        pivots.append(HierarchyPivot(
            name = ReadFixedString(file),
            parentID = ReadLong(file),
            position = ReadVector(file),
            eulerAngles = ReadVector(file),
            rotation = ReadQuaternion(file)))
    return pivots
  
# TODO: this isnt correct anymore i think  
# if the exported pivots are corrupted these fixups are used
def read_pivot_fixups(file, chunkEnd):
    pivot_fixups = []
    while file.tell() < chunkEnd:
        pivot_fixups.append(ReadVector(file))
    return pivot_fixups
    
def read_hierarchy(self, file, chunkEnd):
    #print("\n### NEW HIERARCHY: ###")
    hierarchyHeader = HierarchyHeader()
    Pivots = []
    Pivot_fixups = []

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 257:
            hierarchyHeader = read_hierarchy_header(file)
        elif chunkType == 258:
            Pivots = read_pivots(file, subChunkEnd)
        elif chunkType == 259:
            Pivot_fixups = read_pivot_fixups(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return Hierarchy(header = hierarchyHeader, pivots = Pivots, pivot_fixups = Pivot_fixups)
    
#######################################################################################
# Animation
#######################################################################################

def read_animation_header(file):
    return AnimationHeader(version = GetVersion(ReadLong(file)), name = ReadFixedString(file), 
        hieraName = ReadFixedString(file), numFrames = ReadLong(file), frameRate = ReadLong(file))

def read_animation_channel(self, file, chunkEnd):
    #print("Channel")
    firstFrame = ReadShort(file)
    lastFrame = ReadShort(file)
    vectorLen = ReadShort(file)
    type = ReadShort(file)
    pivot = ReadShort(file)
    pad = ReadShort(file) 

    data = []
    if vectorLen == 1:
        while file.tell() < chunkEnd:
            data.append(ReadFloat(file))
    elif vectorLen == 4:
        while file.tell() < chunkEnd:
            data.append(ReadQuaternion(file))
    else:
        skip_unknown_chunk(self, file, chunkType, chunkSize)

    return AnimationChannel(firstFrame = firstFrame, lastFrame = lastFrame, vectorLen = vectorLen, 
        type = type, pivot = pivot, pad = pad, data = data)

def read_animation(self, file, chunkEnd):
    print("\n### NEW ANIMATION: ###")
    header = AnimationHeader()
    channels = []

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 513:
            header = read_animation_header(file)
        elif chunkType == 514:
            channels.append(read_animation_channel(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return Animation(header = header, channels = channels)

def read_compressed_animation_header(file):
    return CompressedAnimationHeader(version = GetVersion(ReadLong(file)), name = ReadFixedString(file), 
        hieraName = ReadFixedString(file), numFrames = ReadLong(file), frameRate = ReadShort(file), flavor = ReadShort(file))

def read_time_coded_animation_channel(self, file, chunkEnd): # bfme I animation struct
    timeCodesCount = ReadLong(file)
    pivot = ReadShort(file)
    vectorLen = ReadUnsignedByte(file)
    type = ReadUnsignedByte(file)
    timeCodedKeys = []

    while file.tell() < chunkEnd: 
        key = TimeCodedAnimationKey()
        key.frame = ReadLong(file)

        if type == 6:
            key.value = ReadQuaternion(file)
        else:
            key.value = ReadFloat(file)
        timeCodedKeys.append(Key)

    return TimeCodedAnimationChannel(timeCodesCount = timeCodesCount, pivot = pivot, vectorLen = vectorLen, type = type,
        timeCodedKeys = timeCodedKeys)

def read_time_coded_bit_channel(self, file, chunkEnd): #-- channel of boolean values (e.g. visibility) - always size 16
    timeCodesCount = ReadLong(file)
    pivot = ReadShort(file)
    type = ReadUnsignedByte(file) #0 = vis, 1 = timecoded vis
    defaultValue = ReadUnsignedByte(file)

    values = []

    #8 bytes left
    while file.tell() < chunkEnd:
        # dont yet know how to interpret this data
        print(ReadUnsignedByte(file))

def read_time_coded_animation_vector(self, file, chunkEnd):
    print("##############") 
    zero = ReadUnsignedByte(file)
    delta = ReadUnsignedByte(file)
    vecLen = ReadUnsignedByte(file)
    flag = ReadUnsignedByte(file)
    count = ReadShort(file)
    pivot = ReadShort(file)

    print(zero, delta, vecLen, flag, count, pivot)

    if delta == 0:  
        for x in range(0, count):
            print(ReadUnsignedShort(file))

        print("### data")
        #skip 2 bytes if uneven
        if (count % 2) > 0: 
            file.read(2)

        print ("remaining bytes: ", chunkEnd - file.tell())

        for x in range(0, count * vecLen):
            print(ReadFloat(file))

    elif delta == 1:
        print(ReadFloat(file))
        for x in range(0, vecLen):
            print(ReadFloat(file))
        while file.tell() < chunkEnd:
            print(ReadUnsignedByte(file))
    else:
        while file.tell() < chunkEnd:
            file.read(1)

def read_compressed_animation(self, file, chunkEnd):
    print("\n### NEW COMPRESSED ANIMATION: ###")
    header = CompressedAnimationHeader()
    channels = []
    vectors = []

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 641:
            header = read_compressed_animation_header(file)
        elif chunkType == 642:
            channels.append(read_time_coded_animation_channel(self, file, subChunkEnd))
        elif chunkType == 643:
            print("chunk 643 not implemented yet")
            file.seek(chunkSize, 1)
        elif chunkType == 644:
            vectors.append(read_time_coded_animation_vector(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)    

    return CompressedAnimation(header = header, channels = channels, vectors = vectors)

#######################################################################################
# HLod
#######################################################################################

def read_hlod_header(file):
    return HLodHeader(
        version = GetVersion(ReadLong(file)),
        lodCount = ReadLong(file),
        modelName = ReadFixedString(file),
        HTreeName = ReadFixedString(file))

def read_hlod_array_header(file):
    return HLodArrayHeader(
        modelCount = ReadLong(file),
        maxScreenSize = ReadFloat(file))

def read_hlod_sub_object(file):
    return HLodSubObject(
        boneIndex = ReadLong(file),
        name = ReadLongFixedString(file))

def read_hlod_array(self, file, chunkEnd):
    hlodArrayHeader = HLodArrayHeader()
    hlodSubObjects = []
    
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))

        if chunkType == 1795:
            hlodArrayHeader = read_hlod_array_header(file)
        elif chunkType == 1796:
            hlodSubObjects.append(read_hlod_sub_object(file))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return HLodArray(header = hlodArrayHeader, subObjects = hlodSubObjects)

def read_hlod(self, file, chunkEnd):
    #print("\n### NEW HLOD: ###")
    hlodHeader = HLodHeader()
    hlodArray = HLodArray()

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 1793:
            hlodHeader = read_hlod_header(file)
        elif chunkType == 1794:
            hlodArray = read_hlod_array(self, file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return HLod(header = hlodHeader, lodArray = hlodArray)
    
#######################################################################################
# Box
####################################################################################### 

def read_box(file):
    #print("\n### NEW BOX: ###")
    return Box(
        version = GetVersion(ReadLong(file)), 
        attributes = ReadLong(file), 
        name = ReadLongFixedString(file), 
        color = ReadRGBA(file), 
        center = ReadVector(file), 
        extend = ReadVector(file))

#######################################################################################
# Texture
####################################################################################### 

def read_texture(self, file, chunkEnd):
    tex = Texture()
    while file.tell() < chunkEnd:
        chunktype = ReadLong(file)
        chunksize = GetChunkSize(ReadLong(file))

        if chunktype == 50:
            tex.name = ReadString(file)
        elif chunktype == 51:
            tex.textureInfo = TextureInfo(
                attributes = ReadShort(file),
                animType = ReadShort(file), 
                frameCount = ReadLong(file), 
                frameRate = ReadFloat(file))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return tex

def read_texture_array(self, file, chunkEnd):
    textures = []
    
    while file.tell() < chunkEnd:
        chunktype = ReadLong(file)
        chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunksize

        if chunktype == 49:
            textures.append(read_texture(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return textures
    
#######################################################################################
# Material
####################################################################################### 

def read_mesh_texture_coord_array(file, chunkEnd):
    txCoords = []
    while file.tell() < chunkEnd:
        txCoords.append((ReadFloat(file), ReadFloat(file)))
    return txCoords

def read_mesh_texture_stage(self, file, chunkEnd):
    textureIds = []
    textureCoords = []

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 73:
            textureIds = ReadLongArray(file, subChunkEnd)
        elif chunkType == 74:
            textureCoords = read_mesh_texture_coord_array(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshTextureStage(txIds = textureIds, txCoords = textureCoords)   

def read_mesh_material_pass(self, file, chunkEnd):
    # got two different types of material passes depending on if the mesh has bump maps of not
    vertexMaterialIds = []
    shaderIds = []
    DCG =  []
    textureStage = MeshTextureStage()

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 57: 
            certexMaterialIds = ReadLongArray(file, subChunkEnd)
        elif chunkType == 58:
            shaderIds = ReadLongArray(file, subChunkEnd)
        elif chunkType == 59:
            while file.tell() < subChunkEnd:
                DCG.append(ReadRGBA(file))
        elif chunkType == 63:# dont know what this is -> size is always 4 and value 0
            #print("<<< unknown Chunk 63 >>>")
            file.seek(chunkSize, 1)
        elif chunkType == 72: 
            textureStage = read_mesh_texture_stage(self, file, subChunkEnd)
        elif chunkType == 74: 
            textureStage.txCoords = read_mesh_texture_coord_array(file, subChunkEnd)  
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshMaterialPass(vmIds = vertexMaterialIds, shaderIds = shaderIds, dcg = DCG, txStage = textureStage)

def read_material(self, file, chunkEnd):
    material = MeshMaterial()

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))

        if chunkType == 44:
            material.vmName = ReadString(file)
        elif chunkType == 45:
            material.vmInfo = VertexMaterial(
                attributes = ReadLong(file),
                ambient = ReadRGBA(file),
                diffuse = ReadRGBA(file),
                specular = ReadRGBA(file),
                emissive = ReadRGBA(file),
                shininess = ReadFloat(file),
                opacity = ReadFloat(file),
                translucency = ReadFloat(file))
        elif chunkType == 46:
            material.vmArgs0 = ReadString(file)
        elif chunkType == 47:
            material.vmArgs1 = ReadString(file)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return material

def read_mesh_material_array(self, file, chunkEnd):
    materials = []
    
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell()+chunkSize
        
        if chunkType == 43:
            materials.append(read_material(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return materials

def read_mesh_material_set_info(file):
    return MeshMaterialSetInfo(
        passCount = ReadLong(file), 
        vertMatlCount = ReadLong(file), 
        shaderCount = ReadLong(file), 
        textureCount = ReadLong(file))

#######################################################################################
# Vertex Influences
#######################################################################################

def read_mesh_vertex_influences(file, chunkEnd):
    vertInfs = []

    while file.tell()  < chunkEnd:
        vertInf = MeshVertexInfluences(
            boneIdx = ReadShort(file),
            xtraIdx = ReadShort(file),
            boneInf = ReadShort(file)/100,
            xtraInf = ReadShort(file)/100)
        vertInfs.append(vertInf)

    return vertInfs

#######################################################################################
# Faces
####################################################################################### 

def read_mesh_face_array(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append(MeshFace(
            vertIds = (ReadLong(file), ReadLong(file), ReadLong(file)),
            attrs = ReadLong(file),
            normal = ReadVector(file),
            distance = ReadFloat(file)))
    return faces
    
#######################################################################################
# Shader
#######################################################################################

def read_mesh_shader_array(file, chunkEnd):
    shaders = []

    while file.tell() < chunkEnd:
        shader = MeshShader(
            depthCompare = ReadUnsignedByte(file),
            depthMask = ReadUnsignedByte(file),
            colorMask = ReadUnsignedByte(file),
            destBlend = ReadUnsignedByte(file),
            fogFunc = ReadUnsignedByte(file),
            priGradient = ReadUnsignedByte(file),
            secGradient = ReadUnsignedByte(file),
            srcBlend = ReadUnsignedByte(file),
            texturing = ReadUnsignedByte(file),
            detailColorFunc = ReadUnsignedByte(file),
            detailAlphaFunc = ReadUnsignedByte(file),
            shaderPreset = ReadUnsignedByte(file),
            alphaTest = ReadUnsignedByte(file),
            postDetailColorFunc = ReadUnsignedByte(file),
            postDetailAlphaFunc = ReadUnsignedByte(file),
            pad = ReadUnsignedByte(file))
        shaders.append(shader)
        
    return shaders
    
#######################################################################################
# Bump Maps
#######################################################################################

def read_normal_map_header(file, chunkEnd): 
    return MeshNormalMapHeader(
        number = ReadSignedByte(file), 
        typeName = ReadLongFixedString(file), 
        reserved = ReadLong(file))

def read_normal_map_entry_struct(self, file, chunkEnd, entryStruct):
    type = ReadLong(file) #1 texture, 2 bumpScale/ specularExponent, 5 color, 7 alphaTest
    size = ReadLong(file)
    name = ReadString(file)

    if name == "DiffuseTexture":
        entryStruct.unknown = ReadLong(file)
        entryStruct.diffuseTexName = ReadString(file)
    elif name == "NormalMap":
        entryStruct.unknown_nrm = ReadLong(file)
        entryStruct.normalMap = ReadString(file)
    elif name == "BumpScale":
        entryStruct.bumpScale = ReadFloat(file)
    elif name == "AmbientColor":
        entryStruct.ambientColor = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    elif name == "DiffuseColor":
        entryStruct.diffuseColor = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    elif name == "SpecularColor":
        entryStruct.specularColor = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    elif name == "SpecularExponent":
        entryStruct.specularExponent = ReadFloat(file)
    elif name == "AlphaTestEnable":
        entryStruct.alphaTestEnable = ReadUnsignedByte(file)
    else:
        skip_unknown_chunk(self, file, chunkType, chunkSize)

    return entryStruct

def read_normal_map(self, file, chunkEnd):
    header = MeshNormalMapHeader()
    entryStruct = MeshNormalMapEntryStruct()

    while file.tell() < chunkEnd:
        chunktype = ReadLong(file)
        chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize

        if chunktype == 82:
            header = read_normal_map_header(file, subChunkEnd)
        elif chunktype == 83:
            entryStruct = read_normal_map_entry_struct(self, file, subChunkEnd, EntryStruct)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshNormalMap(header = header, entryStruct = entryStruct)

def read_bump_map_array(self, file, chunkEnd):
    normalMap = MeshNormalMap()

    while file.tell() < chunkEnd:
        chunktype = ReadLong(file)
        chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize

        if chunktype == 81:
            normalMap = read_normal_map(self, file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshBumpMapArray(normalMap = normalMap)
    
#######################################################################################
# AABBTree (Axis-aligned-bounding-box-tree)
####################################################################################### 

def read_aabbtree_header(file, chunkEnd):
    nodeCount = ReadLong(file)
    polyCount = ReadLong(file)

    #padding of the header ?
    while file.tell() < chunkEnd:
        file.read(4)

    return AABBTreeHeader(nodeCount = nodeCount, polyCount = polyCount)

def read_aabbtree_poly_indices(file, chunkEnd):
    polyIndices = []

    while file.tell() < chunkEnd:
        polyIndices.append(ReadLong(file))

    return polyIndices

def read_aabbtree_nodes(file, chunkEnd):
    nodes = []

    while file.tell() < chunkEnd:
        nodes.append(AABBTreeNode(
                min = ReadVector(file), 
                max = ReadVector(file) , 
                frontOrPoly0 = ReadLong(file), 
                backOrPolyCount = ReadLong(file)))

    return nodes

def read_aabbtree(self, file, chunkEnd):
    aabbtree = MeshAABBTree()

    while file.tell() < chunkEnd:
        chunktype = ReadLong(file)
        chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize

        if chunktype == 145:
            aabbtree.header = read_aabbtree_header(file, subChunkEnd)
        elif Chunktype == 146:
            aabbtree.polyIndices = read_aabbtree_poly_indices(file, subChunkEnd)
        elif Chunktype == 147:
            aabbtree.nodes = read_aabbtree_nodes(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return aabbtree

#######################################################################################
# Mesh
####################################################################################### 

def read_mesh_header(file):
    return MeshHeader(
        version = GetVersion(ReadLong(file)), 
        attrs =  ReadLong(file), 
        meshName = ReadFixedString(file),
        containerName = ReadFixedString(file),
        faceCount = ReadLong(file),
        vertCount = ReadLong(file), 
        matlCount = ReadLong(file), 
        damageStageCount = ReadLong(file), 
        sortLevel = ReadLong(file),
        prelitVersion = ReadLong(file), 
        futureCount = ReadLong(file),
        vertChannelCount = ReadLong(file), 
        faceChannelCount = ReadLong(file),
        #bounding volumes
        minCorner = ReadVector(file),
        maxCorner = ReadVector(file),
        sphCenter = ReadVector(file),
        sphRadius = ReadFloat(file))

def read_mesh(self, file, chunkEnd):
    mesh_header             = MeshHeader()
    mesh_vertices_infs      = []
    mesh_vertices           = []
    mesh_vertices_copy      = []
    mesh_normals            = []
    mesh_normals_copy       = []
    mesh_tangents           = []
    mesh_binormals          = []
    mesh_faces              = []
    mesh_vertice_materials  = []
    mesh_shade_ids          = []
    mesh_shaders            = []
    mesh_textures           = []
    mesh_userText           = []
    mesh_material_set_info  = MeshMaterialSetInfo()
    mesh_material_pass      = MeshMaterialPass()
    mesh_bump_maps          = MeshBumpMapArray()
    mesh_aabbtree           = MeshAABBTree()

    #print("NEW MESH!")
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 2:
            mesh_vertices = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == 3072:
            mesh_vertices_copy = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == 3:
            mesh_normals = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == 3073:
            mesh_normals_copy = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == 12:
            mesh_userText = ReadString(file)
        elif chunkType == 14:
            mesh_vertices_infs = read_mesh_vertex_influences(file, subChunkEnd)
        elif chunkType == 31:
            mesh_header = read_mesh_header(file)
        elif chunkType == 32:
            mesh_faces = read_mesh_face_array(file, subChunkEnd)
        elif chunkType == 34:   
            mesh_shade_ids = ReadLongArray(file, subChunkEnd)
        elif chunkType == 40:
            mesh_material_set_info = read_mesh_material_set_info(file)
        elif chunkType == 41:
            mesh_shaders = read_mesh_shader_array(file, subChunkEnd)
        elif chunkType == 42:
            mesh_vertice_materials = read_mesh_material_array(self, file, subChunkEnd)
        elif chunkType == 48:
            mesh_textures = read_texture_array(self, file, subChunkEnd)
        elif chunkType == 56:
            mesh_material_pass = read_mesh_material_pass(self, file, subChunkEnd)
        #elif chunkType == 80:
        #    mesh_bump_maps = read_bump_map_array(self, file, subChunkEnd)
        #elif chunkType == 96:
        #    mesh_tangents = read_mesh_vertices_array(file, subChunkEnd)
        #elif chunkType == 97:
        #    mesh_binormals == read_mesh_vertices_array(file, subChunkEnd)
        #elif chunkType == 144:
        #    mesh_aabbtree = read_aabbtree(self, file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)
    
    return Mesh(header = mesh_header, 
                verts = mesh_vertices,
                verts_copy = mesh_vertices_copy,
                normals = mesh_normals,
                normals_copy = mesh_normals_copy,
                vertInfs = mesh_vertices_infs,
                faces = mesh_faces,
                userText = mesh_userText,
                shadeIds = mesh_shade_ids,
                matInfo = mesh_material_set_info,
                shaders = mesh_shaders,
                vertMatls = mesh_vertice_materials,
                textures = mesh_textures,
                matlPass = mesh_material_pass,
                bumpMaps = mesh_bump_maps,
                aabbtree = mesh_aabbtree)

#######################################################################################
# load Skeleton file
#######################################################################################

#TODO: can be combined with load mesh?
def load_skeleton_file(self, sklpath):
    print('\n### SKELETON: ###', sklpath)
    hierarchy = Hierarchy()
    file = open(sklpath, "rb")
    filesize = os.path.getsize(sklpath)

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + chunksize
        
        if chunkType == 256:
            hierarchy = read_hierarchy(self, file, chunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    file.close()

    return hierarchy
    
#######################################################################################
# Load
#######################################################################################

def load(self, context, import_settings):
    """Start the w3d import"""
    print('Loading file', self.filepath)

    file = open(self.filepath, "rb")
    filesize = os.path.getsize(self.filepath)

    print('Filesize' , filesize)

    meshes = []
    hierarchy = Hierarchy()
    animation = Animation()
    compressedAnimation = CompressedAnimation()
    hlod = HLod()
    box = Box()

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + chunkSize

        if chunkType == 0:
            meshes.append(read_mesh(self, file, chunkEnd))
        #elif chunkType == 256:
        #    hierarchy = read_hierarchy(self, file, chunkEnd)
        #elif chunkType == 512:
        #    animation = read_animation(self, file, chunkEnd)
        #elif chunkType == 640:
        #    compressedAnimation = read_compressed_animation(self, file, chunkEnd)
        elif chunkType == 1792:
            hlod = read_hlod(self, file, chunkEnd)
        elif chunkType == 1856:
            box = read_box(file)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    file.close()
    
    #load skeleton (_skl.w3d) file if needed 
    sklpath = ""
    if hlod.header.modelName != hlod.header.HTreeName:
        sklpath = os.path.dirname(self.filepath) + "/" + hlod.header.HTreeName.lower() + ".w3d"
        try:
            hierarchy = load_skeleton_file(self, sklpath)
        except:
            self.report({'ERROR'}, "skeleton file not found: " + hlod.header.HTreeName) 
            print("!!! skeleton file not found: " + hlod.header.HTreeName)

    #create skeleton if needed
    if not hlod.header.modelName == hlod.header.HTreeName:
        amtName = hierarchy.header.name
        found = False
        
        for obj in bpy.data.objects:
            if obj.name == amtName:
                rig = obj
                found = True

        #if not found:
        #    rig = create_armature(self, hierarchy, amtName, hlod.lodArray.subObjects)

        #if len(meshes) > 0:
            #if a mesh is loaded set the armature invisible
            #rig.hide = True
    
    
    for m in meshes:
        faces = []
        
        for f in m.faces:
            faces.append(f.vertIds)
           
        #create the mesh
        mesh = bpy.data.meshes.new(m.header.meshName)
        mesh.from_pydata(m.verts, [], faces)
        mesh.update()
        mesh.validate()
        
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        bm.to_mesh(mesh)
        
        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)
        mesh_ob['userText'] = m.userText
        
    for m in meshes: #need an extra loop because the order of the meshes is random
        mesh_ob = bpy.data.objects[m.header.meshName]
        
        link_object_to_active_scene(mesh_ob)
    
    return {'FINISHED'}