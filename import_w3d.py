# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
import os
from io_mesh_w3d.w3d_structs import *
from io_mesh_w3d.w3d_io_binary import *
from io_mesh_w3d.utils_w3d import *


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
                attributes=read_short(file),
                animationType=read_short(file),
                frameCount=read_long(file),
                frameRate=read_float(file))
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
    perFaceTextureCoords = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_TEXTURE_IDS:
            textureIds = read_long_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_STAGE_TEXCOORDS:
            textureCoords = read_mesh_texture_coord_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_PER_FACE_TEXCOORD_IDS:
            while file.tell() < subChunkEnd:
                perFaceTextureCoords.append(read_vector(file))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshTextureStage(txIds=textureIds, perFaceTexCoords=perFaceTextureCoords, txCoords=textureCoords)


def read_mesh_material_pass(self, file, chunkEnd):
    # got two different types of material passes depending on if the mesh has bump maps of not
    vertexMaterialIds = []
    shaderIds = []
    DCG = []
    DIG = []
    SCG = []
    shaderMatIds = []
    textureStages = []
    txCoords = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_VERTEX_MATERIAL_IDS:
            vertexMaterialIds = read_long_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_SHADER_IDS:
            shaderIds = read_long_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_DCG:
            while file.tell() < subChunkEnd:
                DCG.append(RGBA.read(file))
        elif chunkType == W3D_CHUNK_DIG:
            while file.tell() < subChunkEnd:
                DIG.append(RGBA.read(file))
        elif chunkType == W3D_CHUNK_SCG:
            while file.tell() < subChunkEnd:
                SCG.append(RGBA.read(file))
        elif chunkType == W3D_CHUNK_SHADER_MATERIAL_ID:
            while file.tell() < subChunkEnd:
                shaderMatIds.append(read_long(file))
        elif chunkType == W3D_CHUNK_TEXTURE_STAGE:
            texStage = read_mesh_texture_stage(self, file, subChunkEnd)
            textureStages.append(texStage)
        elif chunkType == W3D_CHUNK_STAGE_TEXCOORDS:
            txCoords = read_mesh_texture_coord_array(
                file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return MeshMaterialPass(vmIds=vertexMaterialIds, shaderIds=shaderIds, dcg=DCG, dig=DIG, scg=SCG, shaderMaterialIds=shaderMatIds, txCoords=txCoords, txStages=textureStages)


def read_material(self, file, chunkEnd):
    material = MeshMaterial()

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))

        if chunkType == W3D_CHUNK_VERTEX_MATERIAL_NAME:
            material.vmName = read_string(file)
        elif chunkType == W3D_CHUNK_VERTEX_MATERIAL_INFO:
            material.vmInfo = VertexMaterial(
                attributes=read_long(file),
                ambient=RGBA.read(file),
                diffuse=RGBA.read(file),
                specular=RGBA.read(file),
                emissive=RGBA.read(file),
                shininess=read_float(file),
                opacity=read_float(file),
                translucency=read_float(file))
        elif chunkType == W3D_CHUNK_VERTEX_MAPPER_ARGS0:
            material.vmArgs0 = read_string(file)
        elif chunkType == W3D_CHUNK_VERTEX_MAPPER_ARGS1:
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

        if chunkType == W3D_CHUNK_VERTEX_MATERIAL:
            materials.append(read_material(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return materials


def read_material_info(file):
    return MaterialInfo(
        passCount=read_long(file),
        vertMatlCount=read_long(file),
        shaderCount=read_long(file),
        textureCount=read_long(file))

#######################################################################################
# Vertex Influences
#######################################################################################


def read_mesh_vertex_influences(file, chunkEnd):
    vertInfs = []

    while file.tell() < chunkEnd:
        vertInf = MeshVertexInfluence(
            boneIdx=read_short(file),
            xtraIdx=read_short(file),
            boneInf=read_short(file)/100,
            xtraInf=read_short(file)/100)
        vertInfs.append(vertInf)

    return vertInfs

#######################################################################################
# Faces
#######################################################################################


def read_mesh_triangle_array(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append(MeshTriangle(
            vertIds=(read_long(file), read_long(file), read_long(file)),
            attrs=read_long(file),
            normal=read_vector(file),
            distance=read_float(file)))
    return faces

#######################################################################################
# Shader
#######################################################################################


def read_mesh_shader_array(file, chunkEnd):
    shaders = []

    while file.tell() < chunkEnd:
        shader = MeshShader(
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
        shaders.append(shader)

    return shaders

#######################################################################################
# Shader Material
#######################################################################################


def read_shader_material_header(file, chunkEnd):
    return ShaderMaterialHeader(
        number=read_unsigned_byte(file),
        typeName=read_long_fixed_string(file),
        reserved=read_long(file))


def read_shader_material_property(self, file, chunkEnd):
    type_ = read_long(file)
    read_long(file)  # num available chars
    name_ = read_string(file)

    value_ = None

    if type_ == 1:
        read_long(file)  # num available chars
        value_ = read_string(file)
    elif type_ == 2:
        value_ = read_float(file)
    elif type_ == 4:
        value_ = read_vector(file)
    elif type_ == 5:
        value_ = RGBA.read_f(file)
    elif type_ == 6:
        value_ = read_long(file)
    elif type_ == 7:
        value_ = read_unsigned_byte(file)

    return ShaderMaterialProperty(
        type=type_,
        name=name_,
        value=value_)


def read_shader_material(self, file, chunkEnd):
    header = ShaderMaterialHeader()
    props = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_SHADER_MATERIAL_HEADER:
            header = read_shader_material_header(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_SHADER_MATERIAL_PROPERTY:
            props.append(read_shader_material_property(
                self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return ShaderMaterial(header=header, properties=props)


def read_shader_materials_array(self, file, chunkEnd):
    shaderMaterials = []

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_SHADER_MATERIAL:
            shaderMaterials.append(
                read_shader_material(self, file, subChunkEnd))
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return shaderMaterials

#######################################################################################
# AABBTree (Axis-aligned-bounding-box-tree)
#######################################################################################


def read_aabbtree_header(file, chunkEnd):
    nodeCount = read_long(file)
    polyCount = read_long(file)

    file.read(24) #padding

    return AABBTreeHeader(nodeCount=nodeCount, polyCount=polyCount)


def read_aabbtree_poly_indices(file, chunkEnd):
    polyIndices = []

    while file.tell() < chunkEnd:
        polyIndices.append(read_long(file))

    return polyIndices


def read_aabbtree_nodes(file, chunkEnd):
    nodes = []

    while file.tell() < chunkEnd:
        nodes.append(AABBTreeNode(
            min=read_vector(file),
            max=read_vector(file),
            frontOrPoly0=read_long(file),
            backOrPolyCount=read_long(file)))

    return nodes


def read_aabbtree(self, file, chunkEnd):
    aabbtree = MeshAABBTree()

    while file.tell() < chunkEnd:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_AABBTREE_HEADER:
            aabbtree.header = read_aabbtree_header(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_AABBTREE_POLYINDICES:
            aabbtree.polyIndices = read_aabbtree_poly_indices(
                file, subChunkEnd)
        elif chunkType == W3D_CHUNK_AABBTREE_NODES:
            aabbtree.nodes = read_aabbtree_nodes(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return aabbtree

#######################################################################################
# Mesh
#######################################################################################


def read_mesh_header(file):
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


def read_mesh(self, file, chunkEnd):
    mesh_header = MeshHeader()
    mesh_vertices_infs = []
    mesh_vertices = []
    mesh_vertices_2 = []
    mesh_normals = []
    mesh_normals_2 = []
    mesh_tangents = []
    mesh_bitangents = []
    mesh_triangles = []
    mesh_vertice_materials = []
    mesh_shade_ids = []
    mesh_shaders = []
    mesh_textures = []
    mesh_userText = []
    mesh_shader_materials = []
    mesh_material_info = MaterialInfo()
    mesh_material_pass = MeshMaterialPass()
    mesh_aabbtree = MeshAABBTree()

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
        elif chunkType == W3D_CHUNK_VERTEX_SHADE_INDICES:
            mesh_shade_ids = read_long_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_MATERIAL_INFO:
            mesh_material_info = read_material_info(file)
        elif chunkType == W3D_CHUNK_SHADERS:
            mesh_shaders = read_mesh_shader_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_VERTEX_MATERIALS:
            mesh_vertice_materials = read_mesh_material_array(
                self, file, subChunkEnd)
        elif chunkType == W3D_CHUNK_TEXTURES:
            mesh_textures = read_texture_array(self, file, subChunkEnd)
        elif chunkType == W3D_CHUNK_MATERIAL_PASS:
            mesh_material_pass = read_mesh_material_pass(
                self, file, subChunkEnd)
        elif chunkType == W3D_CHUNK_SHADER_MATERIALS:
            mesh_shader_materials = read_shader_materials_array(
                self, file, subChunkEnd)
        elif chunkType == W3D_CHUNK_TANGENTS:
            mesh_tangents = read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_BITANGENTS:
            mesh_bitangents == read_mesh_vertices_array(file, subChunkEnd)
        elif chunkType == W3D_CHUNK_AABBTREE:
            mesh_aabbtree = read_aabbtree(self, file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return Mesh(header=mesh_header,
                verts=mesh_vertices,
                verts_2=mesh_vertices_2,
                normals=mesh_normals,
                normals_2=mesh_normals_2,
                vertInfs=mesh_vertices_infs,
                triangles=mesh_triangles,
                tangents=mesh_tangents,
                bitangents=mesh_bitangents,
                userText=mesh_userText,
                shadeIds=mesh_shade_ids,
                matInfo=mesh_material_info,
                shaders=mesh_shaders,
                vertMatls=mesh_vertice_materials,
                textures=mesh_textures,
                materialPass=mesh_material_pass,
                shaderMaterials=mesh_shader_materials,
                aabbtree=mesh_aabbtree)

#######################################################################################
# load Skeleton file
#######################################################################################


def load_skeleton_file(self, sklpath):
    #TODO: handle file not found
    print('\n### SKELETON: ###', sklpath)
    hierarchy = Hierarchy()
    path = insensitive_path(sklpath)
    file = open(path, "rb")
    filesize = os.path.getsize(path)

    while file.tell() < filesize:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        chunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_HIERARCHY:
            hierarchy = Hierarchy.read(self, file, chunkEnd)
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

    print('Filesize', filesize)

    meshes = []
    hierarchy = None
    animation = None
    compressedAnimation = None
    hlod = None
    box = None

    while file.tell() < filesize:
        chunkType = read_long(file)
        chunkSize = get_chunk_size(read_long(file))
        chunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_MESH:
            meshes.append(read_mesh(self, file, chunkEnd))
        elif chunkType == W3D_CHUNK_HIERARCHY:
            hierarchy = Hierarchy.read(self, file, chunkEnd)
        elif chunkType == W3D_CHUNK_ANIMATION:
            animation = Animation.read(self, file, chunkEnd)
        elif chunkType == W3D_CHUNK_COMPRESSED_ANIMATION:
            compressedAnimation = CompressedAnimation.read(
                self, file, chunkEnd)
        elif chunkType == W3D_CHUNK_HLOD:
            hlod = HLod.read(self, file, chunkEnd)
        elif chunkType == W3D_CHUNK_BOX:
           box = Box.read(file)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    file.close()

    create_box(box)

    if (hierarchy == None):
        sklpath = None
        if hlod != None and hlod.header.modelName != hlod.header.hierarchyName:
            sklpath = os.path.dirname(self.filepath) + "/" + \
                hlod.header.hierarchyName.lower() + ".w3d"
        elif animation != None and animation.header.name != "":
            sklpath = os.path.dirname(self.filepath) + "/" + \
                animation.header.hierarchyName.lower() + ".w3d"
        elif compressedAnimation != None and compressedAnimation.header.name != "":
            sklpath = os.path.dirname(self.filepath) + "/" + \
                compressedAnimation.header.hierarchyName.lower() + ".w3d"

        if sklpath != None:
            try:
                hierarchy = load_skeleton_file(self, sklpath)
            except:
                self.report({'ERROR'}, "skeleton file not found: " + sklpath)
                print("!!! skeleton file not found: " + sklpath)

    hide_rig = len(meshes) > 0
    rig = get_or_create_skeleton(hlod, hierarchy, hide_rig)

    for m in meshes:
        triangles = []

        for triangle in m.triangles:
            triangles.append(triangle.vertIds)

        mesh = bpy.data.meshes.new(m.header.meshName)

        # apply hierarchy if it exists
        for i in range(len(m.vertInfs)):
            vert = m.verts[i]
            weight = m.vertInfs[i].boneInf
            if weight == 0.0:
                weight = 1.0

            bone = rig.data.bones[hierarchy.pivots[m.vertInfs[i].boneIdx].name]
            m.verts[i] = bone.matrix_local @ Vector(vert)

        mesh.from_pydata(m.verts, [], triangles)
        mesh.update()
        mesh.validate()

        create_uvlayer(mesh, triangles, m.materialPass.txCoords,
                       m.materialPass.txStages)

        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)
        mesh_ob['userText'] = m.userText

        for vertMat in m.vertMatls:
            mesh.materials.append(create_vert_material(m, vertMat))

        destBlend = 0

        for texture in m.textures:
            load_texture_to_mat(self, texture.name,
                                destBlend, mesh.materials[0])

        create_shader_materials(self, m, mesh)

    amtName = hierarchy.header.name

    for m in meshes:  # need an extra loop because the order of the meshes is random
        mesh_ob = bpy.data.objects[m.header.meshName]

        if hierarchy.header.numPivots > 0:
            if is_skin(m):
                for pivot in hierarchy.pivots:
                    mesh_ob.vertex_groups.new(name=pivot.name)

                for i in range(len(m.vertInfs)):
                    weight = m.vertInfs[i].boneInf
                    if weight == 0.0:
                        weight = 1.0

                    mesh_ob.vertex_groups[m.vertInfs[i].boneIdx].add(
                        [i], weight, 'REPLACE')

                    # two bones are not working yet
                    #mesh_ob.vertex_groups[m.vertInfs[i].xtraIdx].add([i], m.vertInfs[i].xtraInf, 'REPLACE')

                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True

            else:
                for pivot in hierarchy.pivots:
                    if pivot.name == m.header.meshName:
                        mesh_ob.rotation_mode = 'QUATERNION'
                        mesh_ob.location = pivot.position
                        mesh_ob.rotation_euler = pivot.eulerAngles
                        mesh_ob.rotation_quaternion = pivot.rotation

                        if pivot.parentID > 0:
                            parent_pivot = hierarchy.pivots[pivot.parentID]
                            try:
                                mesh_ob.parent = bpy.data.objects[parent_pivot.name]
                            except:
                                mesh_ob.parent = bpy.data.objects[amtName]
                                mesh_ob.parent_bone = parent_pivot.name
                                mesh_ob.parent_type = 'BONE'

        link_object_to_active_scene(mesh_ob)

    create_animation(self, animation, hierarchy, compressed=False)
    create_animation(self, compressedAnimation, hierarchy, compressed=True)

    return {'FINISHED'}
