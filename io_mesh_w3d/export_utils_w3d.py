# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

import bpy
import bmesh
from mathutils import Vector
from io_mesh_w3d.structs.w3d_hlod import *
from io_mesh_w3d.structs.w3d_mesh import *
from io_mesh_w3d.structs.w3d_box import *
from io_mesh_w3d.structs.w3d_hierarchy import *
from io_mesh_w3d.structs.w3d_animation import *


#######################################################################################
# Mesh data
#######################################################################################


def export_meshes(skn_file, hierarchy, rig, container_name):
    mesh_structs = []
    hlod = HLod()
    hlod.header.model_name = container_name
    hlod.header.hierarchy_name = hierarchy.header.name
    hlod.lod_array.sub_objects = []

    mesh_objects = [
        object for object in bpy.context.scene.objects if object.type == 'MESH']

    for mesh_object in mesh_objects:
        if mesh_object.name == "BOUNDINGBOX":
            box = Box(
                name=container_name + "." + mesh_object.name,
                center=mesh_object.location)
            box_mesh = mesh_object.to_mesh(
                preserve_all_data_layers=False, depsgraph=None)
            box.extend = Vector(
                (box_mesh.vertices[0].co.x * 2, box_mesh.vertices[0].co.y * 2, box_mesh.vertices[0].co.z))
            box.write(skn_file)
        else:
            mesh_struct = Mesh()
            header = mesh_struct.header
            header.mesh_name = mesh_object.name
            header.container_name = container_name

            mesh = mesh_object.to_mesh(
                preserve_all_data_layers=False, depsgraph=None)
            triangulate(mesh)

            header.vert_count = len(mesh.vertices)

            for vertex in mesh.vertices:
                vertInf = MeshVertexInfluence()

                if vertex.groups:
                    for index, pivot in enumerate(hierarchy.pivots):
                        if pivot.name == mesh_object.vertex_groups[vertex.groups[0].group].name:
                            vertInf.bone_idx = index
                    vertInf.bone_inf = vertex.groups[0].weight
                    mesh_struct.vert_infs.append(vertInf)

                    bone = rig.pose.bones[hierarchy.pivots[vertInf.bone_idx].name]
                    mesh_struct.verts.append(
                        bone.matrix.inverted() @ vertex.co.xyz)
                    if len(vertex.groups) > 1:
                        for index, pivot in enumerate(hierarchy.pivots):
                            if pivot.name == mesh_object.vertex_groups[vertex.groups[1].group].name:
                                vertInf.xtra_idx = index
                        vertInf.xtra_inf = vertex.groups[1].weight

                    elif len(vertex.groups) > 2:
                        print("Error: max 2 bone influences per vertex supported!")

                if not vertex.groups:
                    mesh_struct.verts.append(vertex.co.xyz)

                mesh_struct.normals.append(vertex.normal)

            header.min_corner = Vector(
                (mesh_object.bound_box[0][0], mesh_object.bound_box[0][1], mesh_object.bound_box[0][2]))
            header.max_corner = Vector(
                (mesh_object.bound_box[6][0], mesh_object.bound_box[6][1], mesh_object.bound_box[6][2]))

            for face in mesh.polygons:
                triangle = MeshTriangle()
                triangle.vert_ids = [face.vertices[0],
                                     face.vertices[1], face.vertices[2]]
                triangle.normal = Vector(face.normal)
                vec1 = mesh.vertices[face.vertices[0]].co.xyz
                vec2 = mesh.vertices[face.vertices[1]].co.xyz
                vec3 = mesh.vertices[face.vertices[2]].co.xyz
                tri_pos = Vector((vec1 + vec2 + vec3)) / 3.0
                triangle.distance = (mesh_object.location - tri_pos).length
                mesh_struct.triangles.append(triangle)

            if mesh_object.vertex_groups:
                header.attrs = 0x00020000  # TODO: use the define from import_utils here

            center, radius = calculate_mesh_sphere(mesh)
            header.sphCenter = center
            header.sphRadius = radius

            header.faceCount = len(mesh_struct.triangles)
            mesh_struct.write(skn_file)
            mesh_structs.append(mesh_struct)

            # HLod stuff
            subObject = HLodSubObject()
            subObject.name = container_name + "." + mesh_object.name
            subObject.bone_index = 0

            if header.attrs == 0x00020000:  # TODO: use the define from import_utils here
                for index, pivot in enumerate(hierarchy.pivots):
                    if pivot.name == mesh_object.name:
                        subObject.bone_index = index
            hlod.lod_array.sub_objects.append(subObject)

    hlod.lod_array.header.model_count = len(hlod.lod_array.sub_objects)
    hlod.write(skn_file)
    return (hlod, mesh_structs)


#######################################################################################
# hierarchy data
#######################################################################################


def create_hierarchy(container_name):
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

    if len(rigs) == 1:
        rig = rigs[0]
        hierarchy.header.name = rig.name
        for bone in rig.pose.bones:
            pivot = HierarchyPivot(
                name=bone.name,
                parentID=0)

            matrix = bone.matrix

            if bone.parent is not None:
                for index, piv in enumerate(hierarchy.pivots):
                    if piv.name == bone.parent.name:
                        pivot.parentID = index
                matrix = bone.parent.matrix.inverted() @ matrix

            (pivot.translation, pivot.rotation, _) = matrix.decompose()

            hierarchy.pivots.append(pivot)
    else:
        hierarchy.header.name = container_name

    mesh_objects = [
        object for object in bpy.context.scene.objects if object.type == 'MESH']

    for mesh_object in mesh_objects:
        # TODO: use a constant here
        if not mesh_object.vertex_groups and mesh_object.name != "BOUNDINGBOX":
            pivot = HierarchyPivot(
                name=mesh_object.name,
                parentID=0,
                translation=mesh_object.location,
                rotation=mesh_object.rotation_quaternion)

            if mesh_object.parent_bone != "":
                for index, piv in enumerate(hierarchy.pivots):
                    if piv.name == mesh_object.parent_bone:
                        pivot.parentID = index

            hierarchy.pivots.append(pivot)

    return (hierarchy, rig)


#######################################################################################
# Animation data
#######################################################################################


def export_animation(ani_file, animation_name, hierarchy):
    ani_struct = Animation(channels=[])
    ani_struct.header.name = animation_name
    ani_struct.header.hierarchy_name = hierarchy.header.name

    start_frame = bpy.data.scenes["Scene"].frame_start
    end_frame = bpy.data.scenes["Scene"].frame_end

    ani_struct.header.num_frames = end_frame + 1 - start_frame
    ani_struct.header.frame_rate = bpy.data.scenes["Scene"].render.fps

    if len(bpy.data.actions) > 1:
        print("Error: too many actions in scene")

    channel = None

    action = bpy.data.actions[0]
    for fcu in action.fcurves:
        pivot_name = fcu.data_path.split('"')[1]
        pivot_index = 0
        for i, pivot in enumerate(hierarchy.pivots):
            if pivot.name == pivot_name:
                pivot_index = i

        channel_type = 0
        vec_len = 1
        index = fcu.array_index
        if "rotation_quaternion" in fcu.data_path:
            channel_type = 6
            vec_len = 4
        else:
            channel_type = index

        if not (channel_type == 6 and index > 0):
            channel = AnimationChannel(
                vector_len=vec_len,
                type=channel_type,
                pivot=pivot_index,
                data=[])

            num_keyframes = len(fcu.keyframe_points)
            channel.data = [None] * num_keyframes
            channel.first_frame = int(fcu.keyframe_points[0].co.x)
            channel.last_frame = int(fcu.keyframe_points[num_keyframes - 1].co.x)

        for i, keyframe in enumerate(fcu.keyframe_points):
            #frame = keyframe.co.x
            value = keyframe.co.y
            if channel_type < 6:
                channel.data[i] = value
            else:
                if channel.data[i] is None:
                    channel.data[i] = Quaternion()
                channel.data[i][index] = value

        if channel_type < 6 or index == 3:
            ani_struct.channels.append(channel)

    ani_struct.write(ani_file)


#######################################################################################
# Helper methods
#######################################################################################


def triangulate(mesh):
    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)
    bmesh.ops.triangulate(b_mesh, faces=b_mesh.faces)
    b_mesh.to_mesh(mesh)
    b_mesh.free()


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


def find_most_distant_point(vertex, vertices):
    result = vertices[0]
    dist = 0
    for x in vertices:
        curr_dist = distance(x, vertex)
        if curr_dist > dist:
            dist = curr_dist
            result = x
    return result


def validate_all_points_inside_sphere(center, radius, vertices):
    for vertex in vertices:
        curr_dist = distance(vertex, center)
        if curr_dist > radius:
            delta = (curr_dist - radius)/2
            radius += delta
            center += (vertex - center).normalized() * delta
    return (center, radius)


def calculate_mesh_sphere(mesh):
    vertices = vertices_to_vectors(mesh.vertices)
    x = find_most_distant_point(vertices[0], vertices)
    y = find_most_distant_point(x, vertices)
    z = (x - y)/2
    center = y + z
    radius = z.length

    return validate_all_points_inside_sphere(center, radius, vertices)
