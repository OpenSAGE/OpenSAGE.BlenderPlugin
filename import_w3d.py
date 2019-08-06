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
        version = get_version(read_long(file)),
        name = read_fixed_string(file),
        pivotCount = read_long(file),
        centerPos = read_vector(file))
        
def read_pivots(file, chunkEnd):
    pivots = []
    while file.tell() < chunkEnd:
        pivots.append(HierarchyPivot(
            name = read_fixed_string(file),
            parentID = read_long(file),
            position = read_vector(file),
            eulerAngles = read_vector(file),
            rotation = read_quaternion(file)))
    return pivots
  
# TODO: this isnt correct anymore i think  
# if the exported pivots are corrupted these fixups are used
def read_pivot_fixups(file, chunkEnd):
    pivot_fixups = []
    while file.tell() < chunkEnd:
        pivot_fixups.append(read_vector(file))
    return pivot_fixups
    
def read_hierarchy(self, file, chunkEnd):
    #print("\n### NEW HIERARCHY: ###")
    hierarchyHeader = HierarchyHeader()
    Pivots = []
    Pivot_fixups = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_HIERARCHY_HEADER:
            hierarchyHeader = read_hierarchy_header(file)
        elif chunkType == W3D_CHUNK_PIVOTS:
            Pivots = read_pivots(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_PIVOT_FIXUPS:
            Pivot_fixups = read_pivot_fixups(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return Hierarchy(header = hierarchyHeader, pivots = Pivots, pivot_fixups = Pivot_fixups)
    
#######################################################################################
# Animation
#######################################################################################

def read_animation_header(file):
    return AnimationHeader(version = get_version(read_long(file)), name = read_fixed_string(file), 
        hieraName = read_fixed_string(file), numFrames = read_long(file), frameRate = read_long(file))

def read_animation_channel(self, file, chunkEnd):
    first_frame = read_short(file)
    last_frame = read_short(file)
    vector_len = read_short(file)
    type_ = read_short(file)
    pivot_ = read_short(file)
    padding_ = read_short(file) 

    data_ = []
    if vector_len == 1:
        while file.tell() < chunkEnd:
            data_.append(read_float(file))
    elif vector_len == 4:
        while file.tell() < chunkEnd:
            data_.append(read_quaternion(file))

    return AnimationChannel(
        firstFrame = first_frame, 
        lastFrame = last_frame, 
        vectorLen = vector_len, 
        type = type_, 
        pivot = pivot_, 
        padding = padding_, 
        data = data_)

def read_animation(self, file, chunkEnd):
    print("\n### NEW ANIMATION: ###")
    header = AnimationHeader()
    channels = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_ANIMATION_HEADER:
            header = read_animation_header(file)
        elif chunkType == W3D_CHUNK_ANIMATION_CHANNEL:
            channels.append(read_animation_channel(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return Animation(header = header, channels = channels)


def read_compressed_animation_header(file):
    return CompressedAnimationHeader(
        version = get_version(read_long(file)), 
        name = read_fixed_string(file), 
        hieraName = read_fixed_string(file), 
        numFrames = read_long(file), 
        frameRate = read_short(file), 
        flavor = read_short(file))

def read_time_coded_animation_channel(self, file, chunkEnd):
    channel = TimeCodedAnimationChannel(
        numTimeCodes = read_long(file),
        pivot = read_short(file),
        vectorLen = read_unsigned_byte(file),
        type = read_unsigned_byte(file))
    
    while file.tell() < chunkEnd:
        if channel.type == 6: 
            channel.data.append(read_quaternion(file))
        else:
            channel.data.append(read_float(file))

    return channel

def read_adaptive_delta_channel(file):
    channel = AdaptiveDeltaAnimationChannel(
        numTimeCodes = read_long(file),
        pivot = read_short(file),
        vectorLen = read_unsigned_byte(file),
        type = read_unsigned_byte(file),
        scale = read_float(file))
    
    if channel.type == 6: 
        channel.initialValue = read_quaternion(file)
    else:
        channel.initialValue = read_float(file)
            
    count = (channel.numTimeCodes + 15) >> 4
    index = 0
    while index < count:
        #TODO
        index += 1

    file.read(3) #read 3 unknown bytes

    return channel

def read_time_coded_bit_channel(file):
    print(1)

def read_motion_channel(file):
    print(1)

def read_compressed_animation(self, file, chunkEnd):
    print("\n### NEW COMPRESSED ANIMATION: ###")
    result = CompressedAnimation()

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_COMPRESSED_ANIMATION_HEADER:
            result.header = read_compressed_animation_header(file)
        elif chunkType == W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL:
            if result.header.flavor == 0:
                result.timeCodedChannels.append(read_time_coded_animation_channel(self, file, subChunkEnd))
            elif result.header.flavor == 1:
                result.adaptiveDeltaChannels.append(read_adaptive_delta_channel(file))
        #elif chunkType == W3D_CHUNK_COMPRESSED_BIT_CHANNEL:
        #    result.timeCodedBitChannels.append(read_time_coded_bit_channel(file))
        #elif chunkType == W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL:
        #    result.motionChannels.append(read_motion_channel(file))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)    

    return result

#######################################################################################
# HLod
#######################################################################################

def read_hlod_header(file):
    return HLodHeader(
        version = get_version(read_long(file)),
        lodCount = read_long(file),
        modelName = read_fixed_string(file),
        hierarchyName = read_fixed_string(file))

def read_hlod_array_header(file):
    return HLodArrayHeader(
        modelCount = read_long(file),
        maxScreenSize = read_float(file))

def read_hlod_sub_object(file):
    return HLodSubObject(
        boneIndex = read_long(file),
        name = read_long_fixed_string(file))

def read_hlod_array(self, file, chunkEnd):
    hlodArrayHeader = HLodArrayHeader()
    hlodSubObjects = []
    
    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))

        if chunkType == W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER:
            hlodArrayHeader = read_hlod_array_header(file)
        elif chunkType == W3D_CHUNK_HLOD_SUB_OBJECT:
            hlodSubObjects.append(read_hlod_sub_object(file))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return HLodArray(header = hlodArrayHeader, subObjects = hlodSubObjects)

def read_hlod(self, file, chunkEnd):
    #print("\n### NEW HLOD: ###")
    hlodHeader = HLodHeader()
    hlodArray = HLodArray()

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_HLOD_HEADER:
            hlodHeader = read_hlod_header(file)
        elif chunkType == W3D_CHUNK_HLOD_LOD_ARRAY:
            hlodArray = read_hlod_array(self, file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return HLod(header = hlodHeader, lodArray = hlodArray)
    
#######################################################################################
# Box
####################################################################################### 

def read_box(file):
    #print("\n### NEW BOX: ###")
    ver = get_version(read_long(file))
    flags = read_long(file)
    return Box(
        version = ver, 
        boxType = (flags & 0b11), 
        collisionTypes = (flags & 0xFF0),
        name = read_long_fixed_string(file), 
        color = read_rgba(file), 
        center = read_vector(file), 
        extend = read_vector(file))

#######################################################################################
# Texture
####################################################################################### 

def read_texture(self, file, chunkEnd):
    tex = Texture()
    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))

        if chunkType == W3D_CHUNK_TEXTURE_NAME:
            tex.name = read_string(file)
        elif chunkType == W3D_CHUNK_TEXTURE_INFO:
            tex.textureInfo = TextureInfo(
                attributes = read_short(file),
                animationType = read_short(file), 
                frameCount = read_long(file), 
                frameRate = read_float(file))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return tex

def read_texture_array(self, file, chunkEnd):
    textures = []
    
    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_TEXTURE:
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
        txCoords.append((read_float(file), read_float(file)))
    return txCoords

def read_mesh_texture_stage(self, file, chunkEnd):
    textureIds = []
    textureCoords = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 73:
            textureIds = read_long_array(file, subChunkEnd)
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
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 57: 
            vertexMaterialIds = read_long_array(file, subChunkEnd)
        elif chunkType == 58:
            shaderIds = read_long_array(file, subChunkEnd)
        elif chunkType == 59:
            while file.tell() < subChunkEnd:
                DCG.append(read_rgba(file))
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
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))

        if chunkType == 44:
            material.vmName = read_string(file)
        elif chunkType == 45:
            material.vmInfo = VertexMaterial(
                attributes = read_long(file),
                ambient = read_rgba(file),
                diffuse = read_rgba(file),
                specular = read_rgba(file),
                emissive = read_rgba(file),
                shininess = read_float(file),
                opacity = read_float(file),
                translucency = read_float(file))
        elif chunkType == 46:
            material.vmArgs0 = read_string(file)
        elif chunkType == 47:
            material.vmArgs1 = read_string(file)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return material

def read_mesh_material_array(self, file, chunkEnd):
    materials = []
    
    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell()+chunkSize
        
        if chunkType == 43:
            materials.append(read_material(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return materials

def read_material_info(file):
    return MaterialInfo(
        passCount = read_long(file), 
        vertMatlCount = read_long(file), 
        shaderCount = read_long(file), 
        textureCount = read_long(file))

#######################################################################################
# Vertex Influences
#######################################################################################

def read_mesh_vertex_influences(file, chunkEnd):
    vertInfs = []

    while file.tell()  < chunkEnd:
        vertInf = MeshVertexInfluences(
            boneIdx = read_short(file),
            xtraIdx = read_short(file),
            boneInf = read_short(file)/100,
            xtraInf = read_short(file)/100)
        vertInfs.append(vertInf)

    return vertInfs

#######################################################################################
# Faces
####################################################################################### 

def read_mesh_triangle_array(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append(MeshTriangle(
            vertIds = (read_long(file), read_long(file), read_long(file)),
            attrs = read_long(file),
            normal = read_vector(file),
            distance = read_float(file)))
    return faces
    
#######################################################################################
# Shader
#######################################################################################

def read_mesh_shader_array(file, chunkEnd):
    shaders = []

    while file.tell() < chunkEnd:
        shader = MeshShader(
            depthCompare = read_unsigned_byte(file),
            depthMask = read_unsigned_byte(file),
            colorMask = read_unsigned_byte(file),
            destBlend = read_unsigned_byte(file),
            fogFunc = read_unsigned_byte(file),
            priGradient = read_unsigned_byte(file),
            secGradient = read_unsigned_byte(file),
            srcBlend = read_unsigned_byte(file),
            texturing = read_unsigned_byte(file),
            detailColorFunc = read_unsigned_byte(file),
            detailAlphaFunc = read_unsigned_byte(file),
            shaderPreset = read_unsigned_byte(file),
            alphaTest = read_unsigned_byte(file),
            postDetailColorFunc = read_unsigned_byte(file),
            postDetailAlphaFunc = read_unsigned_byte(file),
            pad = read_unsigned_byte(file))
        shaders.append(shader)
        
    return shaders
    
#######################################################################################
# Bump Maps
#######################################################################################

def read_normal_map_header(file, chunkEnd): 
    return MeshNormalMapHeader(
        number = read_unsigned_byte(file), 
        typeName = read_long_fixed_string(file), 
        reserved = read_long(file))

def read_normal_map_entry_struct(self, file, chunkEnd, entryStruct):
    chunkType = read_long(file) #1 texture, 2 bumpScale/ specularExponent, 5 color, 7 alphaTest
    chunkSize = read_long(file)
    name = read_string(file)

    if name == "DiffuseTexture":
        entryStruct.unknown = read_long(file)
        entryStruct.diffuseTexName = read_string(file)
    elif name == "NormalMap":
        entryStruct.unknown_nrm = read_long(file)
        entryStruct.normalMap = read_string(file)
    elif name == "BumpScale":
        entryStruct.bumpScale = read_float(file)
    elif name == "AmbientColor":
        entryStruct.ambientColor = (read_float(file), read_float(file), read_float(file), read_float(file))
    elif name == "DiffuseColor":
        entryStruct.diffuseColor = (read_float(file), read_float(file), read_float(file), read_float(file))
    elif name == "SpecularColor":
        entryStruct.specularColor = (read_float(file), read_float(file), read_float(file), read_float(file))
    elif name == "SpecularExponent":
        entryStruct.specularExponent = read_float(file)
    elif name == "AlphaTestEnable":
        entryStruct.alphaTestEnable = read_unsigned_byte(file)
    else:
        skip_unknown_chunk(self, file, chunkType, chunkSize)

    return entryStruct

def read_normal_map(self, file, chunkEnd):
    header = MeshNormalMapHeader()
    entryStruct = MeshNormalMapEntryStruct()

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 82:
            header = read_normal_map_header(file, subChunkEnd)
        elif chunkType == 83:
            entryStruct = read_normal_map_entry_struct(self, file, subChunkEnd, entryStruct)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshNormalMap(header = header, entryStruct = entryStruct)

def read_bump_map_array(self, file, chunkEnd):
    normalMap = MeshNormalMap()

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 81:
            normalMap = read_normal_map(self, file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshBumpMapArray(normalMap = normalMap)
    
#######################################################################################
# AABBTree (Axis-aligned-bounding-box-tree)
####################################################################################### 

def read_aabbtree_header(file, chunkEnd):
    nodeCount = read_long(file)
    polyCount = read_long(file)

    #padding of the header ?
    while file.tell() < chunkEnd:
        file.read(4)

    return AABBTreeHeader(nodeCount = nodeCount, polyCount = polyCount)

def read_aabbtree_poly_indices(file, chunkEnd):
    polyIndices = []

    while file.tell() < chunkEnd:
        polyIndices.append(read_long(file))

    return polyIndices

def read_aabbtree_nodes(file, chunkEnd):
    nodes = []

    while file.tell() < chunkEnd:
        nodes.append(AABBTreeNode(
                min = read_vector(file), 
                max = read_vector(file) , 
                frontOrPoly0 = read_long(file), 
                backOrPolyCount = read_long(file)))

    return nodes

def read_aabbtree(self, file, chunkEnd):
    aabbtree = MeshAABBTree()

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 145:
            aabbtree.header = read_aabbtree_header(file, subChunkEnd)
        elif chunkType == 146:
            aabbtree.polyIndices = read_aabbtree_poly_indices(file, subChunkEnd)
        elif chunkType == 147:
            aabbtree.nodes = read_aabbtree_nodes(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return aabbtree

#######################################################################################
# Mesh
####################################################################################### 

def read_mesh_header(file):
    return MeshHeader(
        version = get_version(read_long(file)), 
        attrs =  read_long(file), 
        meshName = read_fixed_string(file),
        containerName = read_fixed_string(file),
        faceCount = read_long(file),
        vertCount = read_long(file), 
        matlCount = read_long(file), 
        damageStageCount = read_long(file), 
        sortLevel = read_long(file),
        prelitVersion = read_long(file), 
        futureCount = read_long(file),
        vertChannelCount = read_long(file), 
        faceChannelCount = read_long(file),
        #bounding volumes
        minCorner = read_vector(file),
        maxCorner = read_vector(file),
        sphCenter = read_vector(file),
        sphRadius = read_float(file))

def read_mesh(self, file, chunkEnd):
    mesh_header             = MeshHeader()
    mesh_vertices_infs      = []
    mesh_vertices           = []
    mesh_vertices_2         = []
    mesh_normals            = []
    mesh_normals_2          = []
    mesh_tangents           = []
    mesh_binormals          = []
    mesh_triangles          = []
    mesh_vertice_materials  = []
    mesh_shade_ids          = []
    mesh_shaders            = []
    mesh_textures           = []
    mesh_userText           = []
    mesh_material_info      = MaterialInfo()
    mesh_material_pass      = MeshMaterialPass()
    mesh_bump_maps          = MeshBumpMapArray()
    mesh_aabbtree           = MeshAABBTree()

    #print("NEW MESH!")
    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_VERTICES:
            mesh_vertices = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_VERTICES_2:
            mesh_vertices_2 = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_VERTEX_NORMALS:
            mesh_normals = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_NORMALS_2:
            mesh_normals_2 = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_MESH_USER_TEXT:
            mesh_userText = read_string(file)
        elif chunkType == W3D_CHUNK_VERTEX_INFLUENCES:
            mesh_vertices_infs = read_mesh_vertex_influences(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_MESH_HEADER:
            mesh_header = read_mesh_header(file)
        elif chunkType == W3D_CHUNK_TRIANGLES:
            mesh_triangles = read_mesh_triangle_array(file, subChunkEnd)
        elif chunkType == 34:   
            mesh_shade_ids = read_long_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_MATERIAL_INFO:
            mesh_material_set_info = read_material_info(file)
        elif chunkType == 41:
            mesh_shaders = read_mesh_shader_array(file, subChunkEnd)
        elif chunkType == 42:
            mesh_vertice_materials = read_mesh_material_array(self, file, subChunkEnd)
        elif chunkType == W3D_CHUNK_TEXTURES:
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
                verts_2 = mesh_vertices_2,
                normals = mesh_normals,
                normals_2 = mesh_normals_2,
                vertInfs = mesh_vertices_infs,
                triangles = mesh_triangles,
                userText = mesh_userText,
                shadeIds = mesh_shade_ids,
                matInfo = mesh_material_set_info,
                shaders = mesh_shaders,
                vertMatls = mesh_vertice_materials,
                textures = mesh_textures,
                materialPass = mesh_material_pass,
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
        chunkType = read_long(file)
        chunkSize =  get_chunk_size(read_long(file))
        chunkEnd = file.tell() + chunkSize
        
        if chunkType == W3D_CHUNK_HIERARCHY:
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
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        chunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_MESH:
            meshes.append(read_mesh(self, file, chunkEnd))
        elif chunkType == W3D_CHUNK_HIERARCHY:
            hierarchy = read_hierarchy(self, file, chunkEnd)
        #elif chunkType == W3D_CHUNK_ANIMATION:
        #    animation = read_animation(self, file, chunkEnd)
        #elif chunkType == W3D_CHUNK_COMPRESSED_ANIMATION:
        #    compressedAnimation = read_compressed_animation(self, file, chunkEnd)
        elif chunkType == W3D_CHUNK_HLOD:
            hlod = read_hlod(self, file, chunkEnd)
        elif chunkType == W3D_CHUNK_BOX:
            box = read_box(file)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    file.close()
    
    #load skeleton (_skl.w3d) file if needed 
    sklpath = ""
    if hlod.header.modelName != hlod.header.hierarchyName:
        sklpath = os.path.dirname(self.filepath) + "/" + hlod.header.hierarchyName.lower() + ".w3d"
        try:
            hierarchy = load_skeleton_file(self, sklpath)
        except:
            self.report({'ERROR'}, "skeleton file not found: " + hlod.header.hierarchyName) 
            print("!!! skeleton file not found: " + hlod.header.hierarchyName)

    #create skeleton if needed
    if not hlod.header.modelName == hlod.header.hierarchyName:
        amtName = hierarchy.header.name
        found = False
        
        for obj in bpy.data.objects:
            if obj.name == amtName:
                rig = obj
                found = True

        if not found:
            rig = create_armature(self, hierarchy, amtName, hlod.lodArray.subObjects)

        #if len(meshes) > 0:
            #if a mesh is loaded set the armature invisible
        #   rig.hide = True
    
    
    for m in meshes:
        triangles = []
        
        for triangle in m.triangles:
            triangles.append(triangle.vertIds)
           
        #create the mesh
        mesh = bpy.data.meshes.new(m.header.meshName)
        mesh.from_pydata(m.verts, [], triangles)
        mesh.update()
        mesh.validate()
        
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        #create the uv map
        uv_layer = mesh.uv_layers.new()
        
        index = 0
        if len(m.materialPass.txStage.txCoords) > 0:
            for f in bm.faces:
                f.loops[0][uv_layer].uv = m.materialPass.txStage.txCoords[triangles[index][0]]
                f.loops[1][uv_layer].uv = m.materialPass.txStage.txCoords[triangles[index][1]]
                f.loops[2][uv_layer].uv = m.materialPass.txStage.txCoords[triangles[index][2]]
                index+=1
        
        bm.to_mesh(mesh)
        
        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)
        mesh_ob['userText'] = m.userText
        
        destBlend = 0
        
        for texture in m.textures:
            load_texture(self, mesh, texture.name, "diffuse", destBlend)
        
    for m in meshes: #need an extra loop because the order of the meshes is random
        mesh_ob = bpy.data.objects[m.header.meshName]

        if hierarchy.header.pivotCount > 0:
            # mesh header attributes
            #        0      -> normal mesh
            #        8192   -> normal mesh - two sided
            #        32768  -> normal mesh - cast shadow
            #        40960  -> normal mesh - two sided - cast shadow
            #        131072 -> skin
            #        139264 -> skin - two sided
            #        143360 -> skin - two sided - hidden
            #        163840 -> skin - cast shadow
            #        172032 -> skin - two sided - cast shadow
            #        393216 -> normal mesh - camera oriented (points _towards_ camera)
            type = m.header.attrs
            #if type == 8192 or type == 40960 or type == 139264 or type == 143360 or type == 172032:
                #mesh.show_double_sided = True # property not available anymore
            if type == 0 or type == 8192 or type == 32768 or type == 40960 or type == 393216:
                for pivot in hierarchy.pivots:
                    if pivot.name == m.header.meshName:
                        mesh_ob.rotation_mode = 'QUATERNION'
                        mesh_ob.location =  pivot.position
                        mesh_ob.rotation_euler = pivot.eulerAngles
                        mesh_ob.rotation_quaternion = pivot.rotation

                        #test if the pivot has a parent pivot and parent the corresponding bone to the mesh if it has
                        if pivot.parentID > 0:
                            parent_pivot = hierarchy.pivots[pivot.parentID]
                            try:
                                mesh_ob.parent = bpy.data.objects[parent_pivot.name]
                            except:
                                mesh_ob.parent = bpy.data.objects[amtName]
                                mesh_ob.parent_bone = parent_pivot.name
                                mesh_ob.parent_type = 'BONE'

            elif type == 131072 or type == 139264 or type == 143360 or type == 163840 or type == 172032:
                for pivot in hierarchy.pivots:
                    mesh_ob.vertex_groups.new(name=pivot.name)

                for i in range(len(m.vertInfs)):
                    weight = m.vertInfs[i].boneInf
                    if weight == 0.0:
                        weight = 1.0
                        
                    mesh_ob.vertex_groups[m.vertInfs[i].boneIdx].add([i], weight, 'REPLACE')

                    #two bones are not working yet
                    #mesh_ob.vertex_groups[m.vertInfs[i].xtraIdx].add([i], m.vertInfs[i].xtraInf, 'REPLACE')

                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True

                #to keep the transformations while mesh is in edit mode!!!
                mod.show_in_editmode = True
                mod.show_on_cage = True
            else:
                print("unsupported meshtype attribute: %i" %type)
                self.report({'ERROR'}, "unsupported meshtype attribute: %i" %type)
                
        link_object_to_active_scene(mesh_ob)
    
    bpy.context.scene.game_settings.material_mode = 'GLSL'
    
    return {'FINISHED'}