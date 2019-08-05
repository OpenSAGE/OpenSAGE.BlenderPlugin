import bpy
import os
from . import w3d_structs
from . import w3d_io_binary

def read_mesh_header(file):
    result = w3d_structs.MeshHeader(
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
        sphRadius =	 ReadFloat(file))
    return result

def read_mesh(file, chunkEnd):
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

    
    return w3d_structs.Mesh(verts = mesh_verts)


def load(givenfilepath, context, import_settings):
    """Start the w3d import"""
    print('Loading file', givenfilepath)

    file = open(givenfilepath,"rb")
    filesize = os.path.getsize(givenfilepath)

    meshes = []

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + chunkSize

        if chunkType == 0:
            m = read_mesh(file, chunkEnd)
            meshes.append(m)
            file.seek(chunkEnd,0)

    return {'FINISHED'}