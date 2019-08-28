# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

import bpy
import bmesh
from mathutils import Vector, Quaternion
from io_mesh_w3d.w3d_structs import *


#######################################################################################
# Mesh data
#######################################################################################


def export_meshes(sknFile, hierarchy, rig, containerName):
    hlod = HLod()
    hlod.header.modelName = containerName
    hlod.header.hierarchyName = hierarchy.header.name
    hlod.lodArray.subObjects = []

    mesh_objects = [
        object for object in bpy.context.scene.objects if object.type == 'MESH']

    for mesh_object in mesh_objects:
        if mesh_object.name == "BOUNDINGBOX":
            box = Box(
                name=containerName + "." + mesh_object.name,
                center=mesh_object.location)
            box_mesh = mesh_object.to_mesh(
                preserve_all_data_layers=False, depsgraph=None)
            box.extend = Vector(
                (box_mesh.vertices[0].co.x * 2, box_mesh.vertices[0].co.y * 2, box_mesh.vertices[0].co.z))
            box.write(sknFile)
        else:
            mesh_struct = Mesh()
            header = mesh_struct.header
            header.meshName = mesh_object.name
            header.containerName = containerName

            mesh = mesh_object.to_mesh(
                preserve_all_data_layers=False, depsgraph=None)
            triangulate(mesh)

            header.vertCount = len(mesh.vertices)

            for v in mesh.vertices:
                vertInf = MeshVertexInfluence()

                if len(v.groups) > 0:
                    for index, pivot in enumerate(hierarchy.pivots):
                        if pivot.name == mesh_object.vertex_groups[v.groups[0].group].name:
                            vertInf.boneIdx = index
                    vertInf.boneInf = v.groups[0].weight
                    mesh_struct.vertInfs.append(vertInf)

                    bone = rig.pose.bones[hierarchy.pivots[vertInf.boneIdx].name]
                    vertex = bone.matrix.inverted() @ v.co.xyz
                    mesh_struct.verts.append(vertex)
                if len(v.groups) > 1:
                    for index, pivot in enumerate(hierarchy.pivots):
                        if pivot.name == mesh_object.vertex_groups[v.groups[1].group].name:
                            vertInf.xtraIdx = index
                    vertInf.xtraInf = v.groups[1].weight

                elif len(v.groups) > 2: 
                    print("Error: max 2 bone influences per vertex supported!")
               
                if len(v.groups) == 0:
                    mesh_struct.verts.append(v.co.xyz)

                mesh_struct.normals.append(v.normal)


            header.minCorner = Vector(
                (mesh_object.bound_box[0][0], mesh_object.bound_box[0][1], mesh_object.bound_box[0][2]))
            header.maxCorner = Vector(
                (mesh_object.bound_box[6][0], mesh_object.bound_box[6][1], mesh_object.bound_box[6][2]))

            for face in mesh.polygons:
                triangle = MeshTriangle()
                triangle.vertIds = [face.vertices[0],
                                    face.vertices[1], face.vertices[2]]
                triangle.normal = face.normal
                tri_pos = Vector(
                    (mesh.vertices[face.vertices[0]].co.xyz + mesh.vertices[face.vertices[1]].co.xyz + mesh.vertices[face.vertices[2]].co.xyz)) / 3.0
                triangle.distance = (mesh_object.location - tri_pos).length
                mesh_struct.triangles.append(triangle)

            if len(mesh_object.vertex_groups) > 0:
                header.attrs = 0x00020000  # TODO: use the define from import_utils here

            center, radius = calculate_mesh_sphere(mesh)
            header.sphCenter = center
            header.sphRadius = radius

            header.faceCount = len(mesh_struct.triangles)
            mesh_struct.write(sknFile)

            # HLod stuff
            subObject = HLodSubObject()
            subObject.name = containerName + "." + mesh_object.name
            subObject.boneIndex = 0

            if header.attrs == 0x00020000:  # TODO: use the define from import_utils here
                for index, pivot in enumerate(hierarchy.pivots):
                    if pivot.name == mesh_object.name:
                        subObject.boneIndex = index
            hlod.lodArray.subObjects.append(subObject)

    hlod.lodArray.header.modelCount = len(hlod.lodArray.subObjects)
    hlod.write(sknFile)


#######################################################################################
# hierarchy data
#######################################################################################


def create_hierarchy(containerName):
    hierarchy = Hierarchy(
            header=HierarchyHeader(),
            pivots=[])
    root = HierarchyPivot(
        name="ROOTTRANSFORM",
        parentID=-1)

    hierarchy.pivots.append(root)

    rigs = [object for object in bpy.context.scene.objects if object.type == 'ARMATURE']

    if len(rigs) > 1:
        print("Error: only one armature per scene allowed")
        return
    elif len(rigs) == 1:
        rig = rigs[0]
        hierarchy.header.name = rig.name
        for bone in rig.pose.bones:
            pivot = HierarchyPivot(
                name=bone.name,
                parentID=0)

            matrix = bone.matrix

            if bone.parent != None:
                for index, p in enumerate(hierarchy.pivots):
                    if p.name == bone.parent.name:
                        pivot.parentID = index
                matrix = bone.parent.matrix.inverted() @ matrix

            (pivot.translation, pivot.rotation, _) = matrix.decompose()

            hierarchy.pivots.append(pivot)
    else:
        hierarchy.header.name = containerName


    mesh_objects = [
        object for object in bpy.context.scene.objects if object.type == 'MESH']

    for mesh_object in mesh_objects:
        if len(mesh_object.vertex_groups) == 0:
            pivot = HierarchyPivot(
                name=mesh_object.name,
                parentID=0,
                translation=mesh_object.location,
                rotation=mesh_object.rotation_quaternion)

            if mesh_object.parent_bone != "":
                for index, p in enumerate(hierarchy.pivots):
                    if p.name == mesh_object.parent_bone:
                        pivot.parentID = index

            hierarchy.pivots.append(pivot)

    return (hierarchy, rig)


#######################################################################################
# Animation data
#######################################################################################


def export_animations(animationName, hierarchy):
    ani_struct = Animation()
    ani_struct.header.name = animationName
    ani_struct.header.hierarchyName = hierarchy.header.name
    ani_struct.header.numFrames = bpy.data.scenes["Scene"].frame_end - \
        bpy.data.scenes["Scene"].frame_start
    ani_struct.header.frameRate = bpy.data.scenes["Scene"].render.fps


#######################################################################################
# Helper methods
#######################################################################################


def triangulate(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()


def vertices_to_vectors(vertices):
    vectors = []
    for vert in vertices:
        vectors.append(Vector(vert.co.xyz))
    return vectors


def distance(vec1, vec2):
    x = (vec1.x - vec2.x)**2
    y = (vec1.y - vec2.y)**2
    z = (vec1.z - vec2.z)**2
    return (x + y + z)**(1/2)


def find_most_distant_point(v, vertices):
    result = vertices[0]
    dist = 0
    for x in vertices:
        curr_dist = distance(x, v)
        if curr_dist > dist:
            dist = curr_dist
            result = x
    return result


def validate_all_points_inside_sphere(center, radius, vertices):
    for v in vertices:
        curr_dist = distance(v, center)
        if curr_dist > radius:
            delta = (curr_dist - radius)/2
            radius += delta
            center += (v - center).normalized() * delta
    return (center, radius)


def calculate_mesh_sphere(mesh):
    vertices = vertices_to_vectors(mesh.vertices)
    x = find_most_distant_point(vertices[0], vertices)
    y = find_most_distant_point(x, vertices)
    z = (x - y)/2
    center = y + z
    radius = z.length

    return validate_all_points_inside_sphere(center, radius, vertices)
