import bpy
import os
import bmesh
from io_mesh_w3d.w3d_io_binary import *
from io_mesh_w3d.w3d_structs import *

def skip_unknown_chunk(self, file, chunkType, chunkSize):
    self.report({'ERROR'}, "unknown chunktype in File: %s" % chunkType)
    print("!!!unknown chunktype in File: %s" % chunkType)
    file.seek(chunkSize,1)

def read_mesh_header(file):
    result = MeshHeader(
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
    return result

def read_mesh(self, file, chunkEnd):
    mesh_header = MeshHeader()
    mesh_verts_infs = []
    mesh_verts      = []
    mesh_normals    = []

    print("New mesh!")
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 2:
            mesh_verts = ReadMeshVerticesArray(file, subChunkEnd)
        elif chunkType == 31:
            mesh_header = read_mesh_header(file)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)
    
    return Mesh(verts = mesh_verts)


def load(self, context, import_settings):
    """Start the w3d import"""
    print('Loading file', self.filepath)

    file = open(self.filepath, "rb")
    filesize = os.path.getsize(self.filepath)

    print('Filesize' , filesize)

    meshes = []

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + chunkSize

        if chunkType == 0:
            m = read_mesh(self, file, chunkEnd)
            meshes.append(m)
            file.seek(chunkEnd,0)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    file.close()
    
    for m in meshes:
        vertices = m.verts 
        faces = []
        
        for f in m.faces:
            faces.append(f.vertIds)
           
        #create the mesh
        mesh = bpy.data.meshes.new(m.header.meshName)
        mesh.from_pydata(vertices, [], faces)
        #mesh.uv_textures.new("UVW")
        
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        #create the uv map
        #uv_layer = bm.loops.layer.uv.verify()
        #bm.faces.layers.tex.verify()
        
        bm.to_mesh(mesh)
        
        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)
        mesh_ob['userText'] = m.userText
    
    return {'FINISHED'}