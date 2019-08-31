# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
from io_mesh_w3d.w3d_structs import *
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.import_utils_w3d import *
from io_mesh_w3d.w3d_adaptive_delta import decode


#######################################################################################
# skeleton
#######################################################################################


def load_skeleton_file(self, sklpath):
    hierarchy = Hierarchy()
    path = insensitive_path(sklpath)
    file = open(path, "rb")
    filesize = os.path.getsize(path)

    while file.tell() < filesize:
        (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

        if chunk_type == W3D_CHUNK_HIERARCHY:
            hierarchy = Hierarchy.read(self, file, chunk_end)
        else:
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

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
        (chunk_type, chunk_size, chunk_end) = read_chunk_head(file)

        if chunk_type == W3D_CHUNK_MESH:
            meshes.append(Mesh.read(self, file, chunk_end))
        elif chunk_type == W3D_CHUNK_HIERARCHY:
            hierarchy = Hierarchy.read(self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_ANIMATION:
            animation = Animation.read(self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION:
            compressedAnimation = CompressedAnimation.read(
                self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_HLOD:
            hlod = HLod.read(self, file, chunk_end)
        elif chunk_type == W3D_CHUNK_BOX:
            box = Box.read(file)
        elif chunk_type == W3D_CHUNK_MORPH_ANIMATION:
            print("-> morph animation chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_HMODEL:
            print("-> hmodel chnuk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LODMODEL:
            print("-> lodmodel chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_COLLECTION:
            print("-> collection chunk not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_POINTS:
            print("-> points chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LIGHT:
            print("-> light chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_EMITTER:
            print("-> emitter chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_AGGREGATE:
            print("-> aggregate chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_NULL_OBJECT:
            print("-> null object chunkt is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_LIGHTSCAPE:
            print("-> lightscape chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_DAZZLE:
            print("-> dazzle chunk is not supported")
            file.seek(chunk_size, 1)
        elif chunk_type == W3D_CHUNK_SOUNDROBJ:
            print("-> soundobj chunk is not supported")
            file.seek(chunk_size, 1)
        else:
            skip_unknown_chunk(self, file, chunk_type, chunk_size)

    file.close()

    # Create a collection
    coll = None
    if hlod is not None:
        coll = bpy.data.collections.new(hlod.header.modelName)
        bpy.context.collection.children.link(coll)

    create_box(box, coll)

    if hierarchy is None:
        sklpath = None
        if hlod is not None and hlod.header.modelName != hlod.header.hierarchy_name:
            sklpath = os.path.dirname(self.filepath) + "/" + \
                hlod.header.hierarchy_name.lower() + ".w3d"
        elif animation is not None and animation.header.name != "":
            sklpath = os.path.dirname(self.filepath) + "/" + \
                animation.header.hierarchy_name.lower() + ".w3d"
        elif compressedAnimation is not None and compressedAnimation.header.name != "":
            sklpath = os.path.dirname(self.filepath) + "/" + \
                compressedAnimation.header.hierarchy_name.lower() + ".w3d"

        if sklpath is not None:
            try:
                hierarchy = load_skeleton_file(self, sklpath)
            except:
                self.report({'ERROR'}, "skeleton file not found: " + sklpath)
                print("!!! skeleton file not found: " + sklpath)

    rig = get_or_create_skeleton(hlod, hierarchy, coll)

    for mesh_struct in meshes:
        triangles = []

        for triangle in mesh_struct.triangles:
            triangles.append(triangle.vertIds)

        mesh = bpy.data.meshes.new(mesh_struct.header.meshName)

        # apply hierarchy if it exists
        for i in range(len(mesh_struct.vertInfs)):
            vert = mesh_struct.verts[i]
            weight = mesh_struct.vertInfs[i].boneInf
            if weight == 0.0:
                weight = 1.0

            bone = rig.data.bones[hierarchy.pivots[mesh_struct.vertInfs[i].boneIdx].name]
            mesh_struct.verts[i] = bone.matrix_local @ Vector(vert)

        mesh.from_pydata(mesh_struct.verts, [], triangles)
        mesh.update()
        mesh.validate()

        if mesh_struct.materialPass is not None:
            create_uvlayers(mesh, triangles, mesh_struct.materialPass.txCoords,
                            mesh_struct.materialPass.txStages)

        smooth_mesh(mesh)

        mesh_ob = bpy.data.objects.new(mesh_struct.header.meshName, mesh)
        mesh_ob['UserText'] = mesh_struct.userText

        for vertMat in mesh_struct.vertMatls:
            mesh.materials.append(create_vert_material(mesh_struct, vertMat))

        for texture in mesh_struct.textures:
            load_texture_to_mat(self, texture.name, mesh.materials[0])

        create_shader_materials(self, mesh_struct, mesh)

    for mesh_struct in meshes:  # need an extra loop because the order of the meshes is random
        mesh_ob = bpy.data.objects[mesh_struct.header.meshName]

        if hierarchy is not None and hierarchy.header.numPivots > 0:
            amtName = hierarchy.header.name
            if is_skin(mesh_struct):
                for pivot in hierarchy.pivots:
                    mesh_ob.vertex_groups.new(name=pivot.name)

                for i in range(len(mesh_struct.vertInfs)):
                    weight = mesh_struct.vertInfs[i].boneInf
                    if weight == 0.0:
                        weight = 1.0

                    mesh_ob.vertex_groups[mesh_struct.vertInfs[i].boneIdx].add(
                        [i], weight, 'REPLACE')

                    if mesh_struct.vertInfs[i].xtraIdx != 0:
                        mesh_ob.vertex_groups[mesh_struct.vertInfs[i].xtraIdx].add(
                            [i], mesh_struct.vertInfs[i].xtraInf, 'ADD')

                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True

            else:
                for pivot in hierarchy.pivots:
                    if pivot.name == mesh_struct.header.meshName:
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

    create_animation(animation, hierarchy, compressed=False)
    create_animation(compressedAnimation, hierarchy, compressed=True)

    return {'FINISHED'}
