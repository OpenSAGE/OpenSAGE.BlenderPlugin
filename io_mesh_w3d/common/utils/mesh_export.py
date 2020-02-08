# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from mathutils import Vector, Matrix
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.structs.mesh import *
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.utils.material_export import *


def retrieve_meshes(context, hierarchy, rig, container_name, force_vertex_materials=False):
    mesh_structs = []
    used_textures = []

    switch_to_pose(rig, 'REST')

    depsgraph = bpy.context.evaluated_depsgraph_get()

    for mesh_object in get_objects('MESH'):
        if mesh_object.object_type != 'NORMAL':
            continue

        if mesh_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh_struct = Mesh()
        mesh_struct.header = MeshHeader(
            mesh_name=mesh_object.name,
            container_name=container_name)

        header = mesh_struct.header
        mesh_struct.user_text = mesh_object.userText

        if mesh_object.hide_get():
            header.attrs |= GEOMETRY_TYPE_HIDDEN

        mesh_object = mesh_object.evaluated_get(depsgraph)
        mesh = mesh_object.to_mesh()
        b_mesh = prepare_bmesh(context, mesh)

        (center, radius) = calculate_mesh_sphere(mesh)
        header.sph_center = center
        header.sph_radius = radius

        if mesh.uv_layers:
            mesh_struct.header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT | VERTEX_CHANNEL_BITANGENT
            mesh.calc_tangents()

        header.vert_count = len(mesh.vertices)

        for i, vertex in enumerate(mesh.vertices):
            matrix = Matrix.Identity(4)

            if vertex.groups:
                vert_inf = VertexInfluence()
                for index, pivot in enumerate(hierarchy.pivots):
                    if pivot.name == mesh_object.vertex_groups[vertex.groups[0].group].name:
                        vert_inf.bone_idx = index
                vert_inf.bone_inf = vertex.groups[0].weight

                if len(vertex.groups) > 1:
                    mesh_struct.multi_bone_skinned = True
                    for index, pivot in enumerate(hierarchy.pivots):
                        if pivot.name == mesh_object.vertex_groups[vertex.groups[1].group].name:
                            vert_inf.xtra_idx = index
                    vert_inf.xtra_inf = vertex.groups[1].weight
                mesh_struct.vert_infs.append(vert_inf)

                if vert_inf.bone_idx > 0:
                    matrix = matrix @ rig.data.bones[hierarchy.pivots[vert_inf.bone_idx].name].matrix_local.inverted()
                else:
                    matrix = matrix @ rig.matrix_local.inverted()

                if len(vertex.groups) > 2:
                    context.warning('max 2 bone influences per vertex supported!')

            (_, _, scale) = mesh_object.matrix_local.decompose()
            scaled_vert = vertex.co * scale.x
            mesh_struct.verts.append(matrix @ scaled_vert)

            (_, rotation, _) = matrix.decompose()

            loops = [loop for loop in mesh.loops if loop.vertex_index == i]
            if loops:
                loop = loops[0]
                mesh_struct.normals.append(rotation @ loop.normal)

                if mesh.uv_layers:
                    # in order to adapt to 3ds max orientation
                    mesh_struct.tangents.append((rotation @ loop.bitangent) * -1)
                    mesh_struct.bitangents.append((rotation @ loop.tangent))
            else:
                context.info('the vertex ' + str(i) + ' in mesh ' + mesh_object.name + ' is unconnected!')
                mesh_struct.normals.append(rotation @ vertex.normal)
                if mesh.uv_layers:
                    # only dummys
                    mesh_struct.tangents.append((rotation @ vertex.normal) * -1)
                    mesh_struct.bitangents.append((rotation @ vertex.normal))

            mesh_struct.shade_ids.append(i)

        header.min_corner = Vector(
            (mesh_object.bound_box[0][0],
             mesh_object.bound_box[0][1],
             mesh_object.bound_box[0][2]))
        header.max_corner = Vector(
            (mesh_object.bound_box[6][0],
             mesh_object.bound_box[6][1],
             mesh_object.bound_box[6][2]))

        for poly in mesh.polygons:
            triangle = Triangle(
                vert_ids=list(poly.vertices),
                normal=Vector(poly.normal))

            vec1 = mesh.vertices[poly.vertices[0]].co
            vec2 = mesh.vertices[poly.vertices[1]].co
            vec3 = mesh.vertices[poly.vertices[2]].co
            tri_pos = (vec1 + vec2 + vec3) / 3.0
            triangle.distance = tri_pos.length
            mesh_struct.triangles.append(triangle)

        header.face_count = len(mesh_struct.triangles)

        if mesh_struct.vert_infs:
            header.attrs |= GEOMETRY_TYPE_SKIN

        center, radius = calculate_mesh_sphere(mesh)
        header.sphCenter = center
        header.sphRadius = radius

        tx_stages = []
        for i, uv_layer in enumerate(mesh.uv_layers):
            stage = TextureStage(
                tx_ids=[i],
                tx_coords=[Vector((0.0, 0.0))] * len(mesh_struct.verts))

            for j, face in enumerate(b_mesh.faces):
                for loop in face.loops:
                    vert_index = mesh_struct.triangles[j].vert_ids[loop.index % 3]
                    stage.tx_coords[vert_index] = uv_layer.data[loop.index].uv.copy()
            tx_stages.append(stage)

        b_mesh.free()

        for i, material in enumerate(mesh.materials):
            mat_pass = MaterialPass()

            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)

            used_textures = get_used_textures(material, principled, used_textures)

            if context.file_format == 'W3X' or (
                    material.material_type == 'SHADER_MATERIAL' and not force_vertex_materials):
                mat_pass.shader_material_ids = [i]
                if i < len(tx_stages):
                    mat_pass.tx_coords = tx_stages[i].tx_coords
                mesh_struct.shader_materials.append(
                    retrieve_shader_material(context, material, principled))
                mesh_struct.material_passes.append(mat_pass)
            else:
                shader = retrieve_shader(material)

                if i < len(tx_stages):
                    mat_pass.tx_stages.append(tx_stages[i])

                vert_material = retrieve_vertex_material(material)

                tex = None
                if principled.base_color_texture.image is not None:
                    info = TextureInfo()
                    img = principled.base_color_texture.image
                    filepath = os.path.basename(img.filepath)
                    if filepath == '':
                        filepath = img.name + '.dds'
                    tex = Texture(
                        id=img.name,
                        file=filepath,
                        texture_info=info)

                #print('material type: ' + material.material_type)
                if material.material_type == 'VERTEX_MATERIAL':
                    mat_pass.shader_ids = [i]
                    mat_pass.vertex_material_ids = [i]
                    mesh_struct.shaders.append(shader)
                    mesh_struct.vert_materials.append(vert_material)
                    mesh_struct.material_passes.append(mat_pass)
                    if tex is not None:
                        mesh_struct.textures.append(tex)
                else:
                    #print('prelit type: ' + material.prelit_type)
                    if material.prelit_type == 'PRELIT_UNLIT':
                        if  mesh_struct.prelit_unlit is None:
                            mesh_struct.prelit_unlit = PrelitBase(
                                    type=W3D_CHUNK_PRELIT_UNLIT,
                                    shaders=[],
                                    vert_materials=[],
                                    material_passes=[],
                                    textures=[])

                        mat_pass.shader_ids = [len(mesh_struct.prelit_unlit.shaders)]
                        mat_pass.vertex_material_ids = [len(mesh_struct.prelit_unlit.vert_materials)]
                        mesh_struct.prelit_unlit.shaders.append(shader)
                        mesh_struct.prelit_unlit.vert_materials.append(vert_material)
                        mesh_struct.prelit_unlit.material_passes.append(mat_pass)
                        if tex is not None:
                            mesh_struct.prelit_unlit.textures.append(tex)

                    elif material.prelit_type == 'PRELIT_VERTEX':
                        if mesh_struct.prelit_vertex is None:
                            mesh_struct.prelit_vertex = PrelitBase(type=W3D_CHUNK_PRELIT_VERTEX,
                                    shaders=[],
                                    vert_materials=[],
                                    material_passes=[],
                                    textures=[])

                        mat_pass.shader_ids = [len(mesh_struct.prelit_vertex.shaders)]
                        mat_pass.vertex_material_ids = [len(mesh_struct.prelit_vertex.vert_materials)]
                        mesh_struct.prelit_vertex.shaders.append(shader)
                        mesh_struct.prelit_vertex.vert_materials.append(vert_material)
                        mesh_struct.prelit_vertex.material_passes.append(mat_pass)
                        if tex is not None:
                            mesh_struct.prelit_vertex.textures.append(tex)

                    elif material.prelit_type == 'PRELIT_LIGHTMAP_MULTI_PASS':
                        if mesh_struct.prelit_lightmap_multi_pass is None:
                            mesh_struct.prelit_lightmap_multi_pass = PrelitBase(type=W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS,
                                    shaders=[],
                                    vert_materials=[],
                                    material_passes=[],
                                    textures=[])

                        mat_pass.shader_ids = [len(mesh_struct.prelit_lightmap_multi_pass.shaders)]
                        mat_pass.vertex_material_ids = [len(mesh_struct.prelit_lightmap_multi_pass.vert_materials)]
                        mesh_struct.prelit_lightmap_multi_pass.shaders.append(shader)
                        mesh_struct.prelit_lightmap_multi_pass.vert_materials.append(vert_material)
                        mesh_struct.prelit_lightmap_multi_pass.material_passes.append(mat_pass)
                        if tex is not None:
                            mesh_struct.prelit_lightmap_multi_pass.textures.append(tex)

                    elif material.prelit_type == 'PRELIT_LIGHTMAP_MULTI_TEXTURE':     
                        if mesh_struct.prelit_lightmap_multi_texture is None:
                            mesh_struct.prelit_lightmap_multi_texture = PrelitBase(type=W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE,
                                    shaders=[],
                                    vert_materials=[],
                                    material_passes=[],
                                    textures=[])

                        mat_pass.shader_ids = [len(mesh_struct.prelit_lightmap_multi_texture.shaders)]
                        mat_pass.vertex_material_ids = [len(mesh_struct.prelit_lightmap_multi_texture.vert_materials)]
                        mesh_struct.prelit_lightmap_multi_texture.shaders.append(shader)
                        mesh_struct.prelit_lightmap_multi_texture.vert_materials.append(vert_material)
                        mesh_struct.prelit_lightmap_multi_texture.material_passes.append(mat_pass)
                        if tex is not None:
                            mesh_struct.prelit_lightmap_multi_texture.textures.append(tex)


        header.vert_channel_flags = VERTEX_CHANNEL_LOCATION | VERTEX_CHANNEL_NORMAL

        if mesh_struct.shader_materials:
            header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT | VERTEX_CHANNEL_BITANGENT
        else:
            mesh_struct.tangents = []
            mesh_struct.bitangents = []

        if mesh_struct.prelit_unlit is not None:
            # print('prelit unlit')
            mesh_struct.header.attrs |= PRELIT_UNLIT
            prelit = mesh_struct.prelit_unlit
            prelit.mat_info = MaterialInfo(
                pass_count=len(prelit.material_passes),
                vert_matl_count=len(prelit.vert_materials),
                shader_count=len(prelit.shaders),
                texture_count=len(prelit.textures))

        if mesh_struct.prelit_vertex is not None:
            # print('prelit vertex')
            mesh_struct.header.attrs |= PRELIT_VERTEX
            prelit = mesh_struct.prelit_vertex
            prelit.mat_info = MaterialInfo(
                pass_count=len(prelit.material_passes),
                vert_matl_count=len(prelit.vert_materials),
                shader_count=len(prelit.shaders),
                texture_count=len(prelit.textures))

        if mesh_struct.prelit_lightmap_multi_pass is not None:
            # print('prelit lightmap multi pass')
            mesh_struct.header.attrs |= PRELIT_LIGHTMAP_MULTI_PASS
            prelit = mesh_struct.prelit_lightmap_multi_pass
            prelit.mat_info = MaterialInfo(
                pass_count=len(prelit.material_passes),
                vert_matl_count=len(prelit.vert_materials),
                shader_count=len(prelit.shaders),
                texture_count=len(prelit.textures))

        if mesh_struct.prelit_lightmap_multi_texture is not None:
            # print('prelit lightmap multi texture')
            mesh_struct.header.attrs |= PRELIT_LIGHTMAP_MULTI_TEXTURE
            prelit = mesh_struct.prelit_lightmap_multi_texture
            prelit.mat_info = MaterialInfo(
                pass_count=len(prelit.material_passes),
                vert_matl_count=len(prelit.vert_materials),
                shader_count=len(prelit.shaders),
                texture_count=len(prelit.textures))


        if mesh_struct.prelit_unlit is None and mesh_struct.prelit_vertex is None \
                and mesh_struct.prelit_lightmap_multi_pass is None and mesh_struct.prelit_lightmap_multi_texture is None:
            # print('NO PRELIT')
            mesh_struct.mat_info = MaterialInfo(
                pass_count=len(mesh_struct.material_passes),
                vert_matl_count=len(mesh_struct.vert_materials),
                shader_count=len(mesh_struct.shaders),
                texture_count=len(mesh_struct.textures))

        mesh_struct.header.matl_count = max(
            len(mesh_struct.vert_materials), len(mesh_struct.shader_materials))
        mesh_structs.append(mesh_struct)

    switch_to_pose(rig, 'POSE')

    return mesh_structs, used_textures


##########################################################################
# Helper methods
##########################################################################


def prepare_bmesh(context, mesh):
    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    b_mesh = split_multi_uv_vertices(context, mesh, b_mesh)

    bmesh.ops.triangulate(b_mesh, faces=b_mesh.faces)
    b_mesh.to_mesh(mesh)

    return b_mesh


def split_multi_uv_vertices(context, mesh, b_mesh):
    b_mesh.verts.ensure_lookup_table()

    for ver in b_mesh.verts:
        ver.select_set(False)

    for i, uv_layer in enumerate(mesh.uv_layers):
        tx_coords = [None] * len(uv_layer.data)
        for j, face in enumerate(b_mesh.faces):
            for loop in face.loops:
                vert_index = mesh.polygons[j].vertices[loop.index % 3]
                if tx_coords[vert_index] is not None \
                        and tx_coords[vert_index] != uv_layer.data[loop.index].uv:
                    b_mesh.verts[vert_index].select_set(True)
                tx_coords[vert_index] = uv_layer.data[loop.index].uv

    split_edges = [e for e in b_mesh.edges if e.verts[0].select and e.verts[1].select]
    if split_edges:
        bmesh.ops.split_edges(b_mesh, edges=split_edges)
        b_mesh.to_mesh(mesh)
        context.info('mesh vertices have been split because of multiple uv coordinates per vertex!')
    return b_mesh


def vertices_to_vectors(vertices):
    vectors = []
    for vert in vertices:
        vectors.append(Vector(vert.co.xyz))
    return vectors


def distance(vec1, vec2):
    x = (vec1.x - vec2.x) ** 2
    y = (vec1.y - vec2.y) ** 2
    z = (vec1.z - vec2.z) ** 2
    return (x + y + z) ** 0.5


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
    return center, radius


def calculate_mesh_sphere(mesh):
    vertices = vertices_to_vectors(mesh.vertices)
    x = find_most_distant_point(vertices[0], vertices)
    y = find_most_distant_point(x, vertices)
    z = (x - y) / 2
    center = y + z
    radius = z.length

    return validate_all_points_inside_sphere(center, radius, vertices)


def retrieve_aabbtree(verts):
    result = AABBTree(header=AABBTreeHeader())

    compute_aabbtree(result, verts, verts)
    result.header.node_count = len(result.nodes)
    result.header.poly_count = len(result.poly_indices)
    return result


def compute_aabbtree(aabbtree, verts, sublist):
    min = Vector((sublist[0].x, sublist[0].y, sublist[0].z))
    max = Vector((sublist[0].x, sublist[0].y, sublist[0].z))

    for vert in sublist:
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

    delta_x = max.x - min.x
    delta_y = max.y - min.y
    delta_z = max.z - min.z

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
