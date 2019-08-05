import bpy
import os
import bmesh
from io_mesh_w3d.w3d_io_binary import *
from io_mesh_w3d.w3d_structs import *

def skip_unknown_chunk(self, file, chunkType, chunkSize):
    self.report({'ERROR'}, "unknown chunktype in File: %s" % chunkType)
    print("!!!unknown chunktype in File: %s" % chunkType)
    file.seek(chunkSize,1)
    
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
        pivot = HierarchyPivot(
            name = ReadFixedString(file),
            parentID = ReadLong(file),
            position = ReadVector(file),
            eulerAngles = ReadVector(file),
            rotation = ReadQuaternion(file))
        pivots.append(pivot)
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
    pivots = []
    pivot_fixups = []

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 257:
            hierarchyHeader = read_hierarchyHeader(file)
        elif chunkType == 258:
            pivots = read_pivots(file, subChunkEnd)
        elif chunkType == 259:
            pivot_fixups = read_pivot_fixups(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    return Hierarchy(header = hierarchyHeader, pivots = pivots, pivot_fixups = pivot_fixups)
    
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
        subChunkEnd = file.tell() + chunkSize

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
# Faces
#######################################################################################	
    
def read_mesh_face(file):
    return MeshFace(
        vertIds = (ReadLong(file), ReadLong(file), ReadLong(file)),
        attrs = ReadLong(file),
        normal = ReadVector(file),
        distance = ReadFloat(file))

def read_mesh_face_array(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append(read_mesh_face(file))
    return faces
    
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
        sphRadius =	ReadFloat(file))

def read_mesh(self, file, chunkEnd):
    mesh_header = MeshHeader()
    mesh_verts_infs = []
    mesh_verts      = []
    mesh_normals    = []
    mesh_faces      = []

    print("NEW MESH!")
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 2:
            mesh_verts = ReadMeshVerticesArray(file, subChunkEnd)
        elif chunkType == 31:
            mesh_header = read_mesh_header(file)
        elif chunkType == 32:
            mesh_faces = read_mesh_face_array(file, subChunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)
    
    return Mesh(header = mesh_header, 
                verts = mesh_verts,
                faces = mesh_faces)

#######################################################################################
# load Skeleton file
#######################################################################################

def load_skeleton_file(self, sklpath):
    #print("\n### SKELETON: ###")
    hierarchy = Hierarchy()
    file = open(self.filepath, "rb")
    filesize = os.path.getsize(self.filepath)

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        Chunksize =	 GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize
        
        if chunkType == 256:
            hierarchy = read_hierarchy(self, file, chunkEnd)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    file.close()

    return hierarchy
    
#######################################################################################
# create Armature
#######################################################################################

def create_armature(self, hierarchy, amtName, subObjects):
    amt = bpy.data.armatures.new(hierarchy.header.name)
    amt.show_names = True
    
    rig = bpy.data.objects.new(amtName, amt)
    rig.location = hierarchy.header.centerPos
    rig.rotation_mode = 'QUATERNION'
    #rig.show_x_ray = True
    rig.track_axis = "POS_X"
    
    #bpy.context.scene.objects.link(rig) # Link the object to the active scene
    #bpy.context.scene.objects.active = rig
    #bpy.ops.object.mode_set(mode = 'EDIT')
    #bpy.context.scene.update()

    non_bone_pivots = []

    for obj in subObjects: 
        non_bone_pivots.append(hierarchy.pivots[obj.boneIndex])

    #create the bones from the pivots
    for pivot in hierarchy.pivots:
        if non_bone_pivots.count(pivot) > 0:
                continue #do not create a bone

        bone = amt.edit_bones.new(pivot.name)

        if pivot.parentID > 0:
            parent_pivot =	hierarchy.pivots[pivot.parentID]
            parent = amt.edit_bones[parent_pivot.name]
            bone.parent = parent
            size = pivot.position.x

        bone.head = Vector((0.0, 0.0, 0.0))
        #has to point in y direction that the rotation is applied correctly
        bone.tail = Vector((0.0, 0.1, 0.0))

    #pose the bones
    bpy.ops.object.mode_set(mode = 'POSE')
    script_directory = os.path.dirname(os.path.abspath(__file__))

    for pivot in hierarchy.pivots:
        if non_bone_pivots.count(pivot) > 0:
            continue #do not create a bone

        bone = rig.pose.bones[pivot.name]
        bone.location = pivot.position
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_euler = pivot.eulerAngles
        bone.rotation_quaternion = pivot.rotation

    bpy.ops.object.mode_set(mode = 'OBJECT')

    return rig
    
#######################################################################################
# helper methods
#######################################################################################

def link_object_to_active_scene(obj):
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

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
    hlod = HLod()

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + chunkSize

        if chunkType == 0:
            meshes.append(read_mesh(self, file, chunkEnd))
        elif chunkType == 256:
            hierarchy = read_hierarchy(self, file, chunkEnd)
        elif chunkType == 1792:
            hlod = read_hlod(self, file, chunkEnd)
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
        mesh = bpy.data.meshes.new(name=m.header.meshName)
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