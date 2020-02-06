# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.structs.mesh import *
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.utils.material_export import *


def retrieve_meshes(context, hierarchy, rig, container_name, force_vertex_materials=False):
    mesh_structs = []
    used_textures = []

    switch_to_pose(rig, 'REST')

    for mesh_object in get_objects('MESH'):
        if mesh_object.object_type != 'NORMAL':
            continue

        if mesh_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh_struct = Mesh(
            header=MeshHeader(
                attrs=GEOMETRY_TYPE_NORMAL),
            vert_channel_flags=VERTEX_CHANNEL_LOCATION | VERTEX_CHANNEL_NORMAL,
            face_channel_flags=1,
            user_text='',
            verts=[],
            normals=[],
            tangents=[],
            bitangents=[],
            vert_infs=[],
            triangles=[],
            shade_ids=[],
            shaders=[],
            vert_materials=[],
            textures=[],
            material_passes=[],
            shader_materials=[],
            multi_bone_skinned=False)

        header = mesh_struct.header
        header.mesh_name = mesh_object.name
        header.container_name = container_name

        mesh_struct.user_text = mesh_object.userText

        if mesh_object.hide_get():
            header.attrs |= GEOMETRY_TYPE_HIDDEN

        mesh = mesh_object.to_mesh(
            preserve_all_data_layers=False, depsgraph=None)

        triangulate(mesh)
        header.vert_count = len(mesh.vertices)

        (center, radius) = calculate_mesh_sphere(mesh)
        header.sph_center = center
        header.sph_radius = radius

        for i, vertex in enumerate(mesh.vertices):
            if vertex.groups:
                vertInf = VertexInfluence()
                for index, pivot in enumerate(hierarchy.pivots):
                    if pivot.name == mesh_object.vertex_groups[vertex.groups[0].group].name:
                        vertInf.bone_idx = index
                vertInf.bone_inf = vertex.groups[0].weight
                mesh_struct.vert_infs.append(vertInf)

                matrix = None
                if vertInf.bone_idx > 0:
                    matrix = rig.pose.bones[hierarchy.pivots[vertInf.bone_idx].name].matrix
                else:
                    matrix = rig.matrix_local

                mesh_struct.verts.append(
                    matrix.inverted() @ vertex.co.xyz)

                if len(vertex.groups) > 1:
                    mesh_struct.multi_bone_skinned = True
                    for index, pivot in enumerate(hierarchy.pivots):
                        if pivot.name == mesh_object.vertex_groups[vertex.groups[1].group].name:
                            vertInf.xtra_idx = index
                    vertInf.xtra_inf = vertex.groups[1].weight

                if len(vertex.groups) > 2:
                    context.warning('max 2 bone influences per vertex supported!')

            else:
                mesh_struct.verts.append(vertex.co.xyz)

            mesh_struct.normals.append(vertex.normal)
            mesh_struct.shade_ids.append(i)

        header.min_corner = Vector(
            (mesh_object.bound_box[0][0],
             mesh_object.bound_box[0][1],
             mesh_object.bound_box[0][2]))
        header.max_corner = Vector(
            (mesh_object.bound_box[6][0],
             mesh_object.bound_box[6][1],
             mesh_object.bound_box[6][2]))

        if mesh.uv_layers:
            mesh.calc_tangents()
            mesh_struct.header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT | VERTEX_CHANNEL_BITANGENT
            mesh_struct.tangents = [Vector] * len(mesh_struct.normals)
            mesh_struct.bitangents = [Vector] * len(mesh_struct.normals)

        for face in mesh.polygons:
            triangle = Triangle()
            triangle.vert_ids = list(face.vertices)
            triangle.normal = Vector(face.normal)
            vec1 = mesh.vertices[face.vertices[0]].normal
            vec2 = mesh.vertices[face.vertices[1]].normal
            vec3 = mesh.vertices[face.vertices[2]].normal
            tri_pos = (vec1 + vec2 + vec3) / 3.0
            triangle.distance = tri_pos.length
            mesh_struct.triangles.append(triangle)

            if mesh.uv_layers:
                for vert in [mesh.loops[i] for i in face.loop_indices]:
                    # TODO: compute the mean value from the
                    # face-vertex-tangents etc?
                    normal = vert.normal
                    tangent = vert.tangent
                    mesh_struct.tangents[vert.vertex_index] = tangent
                    bitangent = vert.bitangent_sign * normal.cross(tangent)
                    mesh_struct.bitangents[vert.vertex_index] = bitangent

        header.face_count = len(mesh_struct.triangles)

        if mesh_struct.vert_infs:
            header.attrs |= GEOMETRY_TYPE_SKIN

        center, radius = calculate_mesh_sphere(mesh)
        header.sphCenter = center
        header.sphRadius = radius

        b_mesh = bmesh.new()
        b_mesh.from_mesh(mesh)

        tx_stages = []
        multiple_uvs_per_vertex = False
        for i, uv_layer in enumerate(mesh.uv_layers):
            stage = TextureStage(
                tx_ids=[i],
                per_face_tx_coords=[],
                tx_coords=[None] * len(mesh_struct.verts))

            for j, face in enumerate(b_mesh.faces):
                for loop in face.loops:
                    vert_index = mesh_struct.triangles[j].vert_ids[loop.index % 3]
                    if stage.tx_coords[vert_index] is not None \
                            and stage.tx_coords[vert_index] != uv_layer.data[loop.index].uv:
                        multiple_uvs_per_vertex = True
                    stage.tx_coords[vert_index] = uv_layer.data[loop.index].uv
            tx_stages.append(stage)

        if multiple_uvs_per_vertex:
            context.warning('w3d file format does not support multiple uv coords per vertex, try another unwrapping method')

        for i, material in enumerate(mesh.materials):
            mat_pass = MaterialPass(
                vertex_material_ids=[],
                shader_ids=[],
                dcg=[],
                dig=[],
                scg=[],
                shader_material_ids=[],
                tx_stages=[],
                tx_coords=[])

            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)

            used_textures = get_used_textures(material, principled, used_textures)

            if context.file_format == 'W3X' or (
                    material.material_type == 'SHADER_MATERIAL' and not force_vertex_materials):
                mat_pass.shader_material_ids = [i]
                if i < len(tx_stages):
                    mat_pass.tx_coords = tx_stages[i].tx_coords
                mesh_struct.shader_materials.append(
                    retrieve_shader_material(material, principled))

            else:
                # TODO: create prelit material structs if material is prelit
                # set mesh_struct.header.attributes accordingly

                mesh_struct.shaders.append(retrieve_shader(material))
                mat_pass.shader_ids = [i]
                mat_pass.vertex_material_ids = [i]
                if i < len(tx_stages):
                    mat_pass.tx_stages.append(tx_stages[i])
                mesh_struct.vert_materials.append(
                    retrieve_vertex_material(material))

                if principled.base_color_texture.image is not None:
                    info = TextureInfo(
                        attributes=0,
                        animation_type=0,
                        frame_count=0,
                        frame_rate=0.0)
                    img = principled.base_color_texture.image
                    filepath = os.path.basename(img.filepath)
                    if filepath == '':
                        filepath = img.name + '.dds'
                    tex = Texture(
                        id=img.name,
                        file=filepath,
                        texture_info=info)
                    mesh_struct.textures.append(tex)

            mesh_struct.material_passes.append(mat_pass)

        header.vert_channel_flags = VERTEX_CHANNEL_LOCATION | VERTEX_CHANNEL_NORMAL

        if mesh_struct.shader_materials:
            header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT | VERTEX_CHANNEL_BITANGENT
        else:
            mesh_struct.tangents = []
            mesh_struct.bitangents = []

        mesh_struct.mat_info = MaterialInfo(
            pass_count=len(mesh_struct.material_passes),
            vert_matl_count=len(mesh_struct.vert_materials),
            shader_count=len(mesh_struct.shaders),
            texture_count=len(mesh_struct.textures))

        mesh_struct.header.matl_count = max(
            len(mesh_struct.vert_materials), len(mesh_struct.shader_materials))
        mesh_structs.append(mesh_struct)

    switch_to_pose(rig, 'POSE')

    return (mesh_structs, used_textures)


##########################################################################
# Helper methods
##########################################################################


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
    x = (vec1.x - vec2.x) ** 2
    y = (vec1.y - vec2.y) ** 2
    z = (vec1.z - vec2.z) ** 2
    return (x + y + z) ** (1 / 2)


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
            delta = (curr_dist - radius) / 2
            radius += delta
            center += (vertex - center).normalized() * delta
    return (center, radius)


def calculate_mesh_sphere(mesh):
    vertices = vertices_to_vectors(mesh.vertices)
    x = find_most_distant_point(vertices[0], vertices)
    y = find_most_distant_point(x, vertices)
    z = (x - y) / 2
    center = y + z
    radius = z.length

    return validate_all_points_inside_sphere(center, radius, vertices)


def retrieve_aabbtree(verts):
    result = AABBTree(
        header=AABBTreeHeader(),
        poly_indices=[],
        nodes=[])

    compute_aabbtree(result, verts, verts)
    result.header.node_count = len(result.nodes)
    result.header.poly_count = len(result.poly_indices)
    return result


def compute_aabbtree(aabbtree, verts, sublist):
    min = Vector((sublist[0].x, sublist[0].y, sublist[0].z))
    max = Vector((sublist[0].x, sublist[0].y, sublist[0].z))

    for vert in sublist:
        # print('v: ' + str(vert))
        if vert.x < min.x:
            min.x = vert.x
        if vert.y < min.y:
            min.y = vert.y
        if vert.z < min.z:
            min.z = vert.z

        if vert.x > max.x:
            max.x = vert.x
        if vert.y > max.y:
            max.y = vert.y
        if vert.z > max.z:
            max.z = vert.z

    # print('min: ' + str(min))
    # print('max: ' + str(max))

    delta_x = max.x - min.x
    delta_y = max.y - min.y
    delta_z = max.z - min.z

    # print('delta_x: ' + str(delta_x))
    # print('delta_y: ' + str(delta_y))
    # print('delta_z: ' + str(delta_z))

    if delta_x > delta_y:
        if delta_x > delta_z:
            x = min.x + delta_x * 0.5
            left = [v for v in sublist if v.x <= x]
            right = [v for v in sublist if v.x > x]
            if delta_x < 1.0:
                left = sublist
                right = []
            # print('split x: ' + str(x))
            process_childs(aabbtree, verts, min, max, left, right)
        else:
            z = min.z + delta_z * 0.5
            bottom = [v for v in sublist if v.z <= z]
            top = [v for v in sublist if v.z > z]
            if delta_z < 1.0:
                top = sublist
                bottom = []
            # print('split z: ' + str(z))
            process_childs(aabbtree, verts, min, max, bottom, top)
    elif delta_y > delta_z:
        y = min.y + delta_y * 0.5
        front = [v for v in sublist if v.y <= y]
        back = [v for v in sublist if v.y > y]
        if delta_y < 1.0:
            front = sublist
            back = []
        # print('split y: ' + str(y))
        process_childs(aabbtree, verts, min, max, front, back)
    else:
        z = min.z + delta_z * 0.5
        bottom = [v for v in sublist if v.z <= z]
        top = [v for v in sublist if v.z > z]
        if delta_z < 1.0:
            bottom = sublist
            top = []
        # print('split z: ' + str(z))
        process_childs(aabbtree, verts, min, max, bottom, top)


def process_childs(aabbtree, verts, min, max, first, second):
    # print('sizes: ' + str(len(first)) + ' ' + str(len(second)))
    if first and second:
        node = AABBTreeNode(
            min=min,
            max=max,
            polys=None,
            children=Children(front=-1, back=-1))
        aabbtree.nodes.append(node)

        node.children.front = len(aabbtree.nodes)
        compute_aabbtree(aabbtree, verts, first)
        node.children.back = len(aabbtree.nodes)
        compute_aabbtree(aabbtree, verts, second)

        # print('created node:  front ' + str(node.children.front) + ' back ' + str(node.children.back))
        return

    combined = first + second
    node = AABBTreeNode(
        min=min,
        max=max,
        polys=Polys(begin=len(aabbtree.poly_indices), count=len(combined)),
        children=None)
    # print('created node:  begin ' + str(node.polys.begin) + ' count ' + str(node.polys.count))
    aabbtree.nodes.append(node)
    for v in combined:
        aabbtree.poly_indices.append(verts.index(v))

