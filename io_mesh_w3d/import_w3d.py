# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
import os
from io_mesh_w3d.w3d_structs import *
from io_mesh_w3d.w3d_io_binary import *
from io_mesh_w3d.utils_w3d import *
from io_mesh_w3d.w3d_adaptive_delta import decode


#######################################################################################
# skeleton
#######################################################################################


def load_skeleton_file(self, sklpath):
    # TODO: handle file not found
    hierarchy = Hierarchy()
    path = insensitive_path(sklpath)
    file = open(path, "rb")
    filesize = os.path.getsize(path)

    while file.tell() < filesize:
        chunkType = read_ulong(file)
        chunkSize = read_chunk_size(file)
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

    meshes = []
    hierarchy = None
    animation = None
    compressedAnimation = None
    hlod = None
    box = None

    while file.tell() < filesize:
        chunkType = read_ulong(file)
        chunkSize = read_chunk_size(file)
        chunkEnd = file.tell() + chunkSize

        if chunkType == W3D_CHUNK_MESH:
            meshes.append(Mesh.read(self, file, chunkEnd))
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
        elif chunkType == W3D_CHUNK_MORPH_ANIMATION:
            print ("-> morph animation chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_HMODEL:
            print ("-> hmodel chnuk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_LODMODEL:
            print ("-> lodmodel chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_COLLECTION:
            print ("-> collection chunk not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_POINTS:
            print ("-> points chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_LIGHT:
            print ("-> light chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_EMITTER:
            print ("-> emitter chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_AGGREGATE:
            print ("-> aggregate chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_NULL_OBJECT:
            print ("-> null object chunkt is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_LIGHTSCAPE:
            print ("-> lightscape chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_DAZZLE:
            print ("-> dazzle chunk is not supported")
            file.seek(chunkSize, 1)
        elif chunkType == W3D_CHUNK_SOUNDROBJ:
            print ("-> soundobj chunk is not supported")
            file.seek(chunkSize, 1)
        else:
            skip_unknown_chunk(self, file, chunkType, chunkSize)

    file.close()

    # Create a collection
    coll = None
    if hlod != None:
        coll = bpy.data.collections.new(hlod.header.modelName)
        bpy.context.collection.children.link(coll)

        #if hlod.header.modelName == hlod.header.hierarchyName and hierarchy != None:
        #    hierarchy.header.name += ".skl"
            

    create_box(box,coll)

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

    if hlod != None and hlod.header.modelName != hlod.header.hierarchyName and hierarchy != None:
        rig = get_or_create_skeleton(hlod, hierarchy, coll)

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

        create_uvlayers(mesh, triangles, m.materialPass.txCoords,
                        m.materialPass.txStages)

        smooth_mesh(mesh)

        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)
        mesh_ob['UserText'] = m.userText

        for vertMat in m.vertMatls:
            mesh.materials.append(create_vert_material(m, vertMat))

        for texture in m.textures:
            load_texture_to_mat(self, texture.name, mesh.materials[0])

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

                    if m.vertInfs[i].xtraIdx != 0:
                        mesh_ob.vertex_groups[m.vertInfs[i].xtraIdx].add(
                            [i], m.vertInfs[i].xtraInf, 'ADD')

                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True

            else:
                for pivot in hierarchy.pivots:
                    if pivot.name == m.header.meshName:
                        mesh_ob.rotation_mode = 'QUATERNION'
                        mesh_ob.location = pivot.translation
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

        link_object_to_active_scene(mesh_ob, coll)

    create_animation(self, animation, hierarchy, compressed=False)
    create_animation(self, compressedAnimation, hierarchy, compressed=True)

    return {'FINISHED'}
