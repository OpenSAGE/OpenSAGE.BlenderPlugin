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

    naming_error = False
    bone_names = [bone.name for bone in rig.pose.bones] if rig is not None else []

    switch_to_pose(rig, 'REST')

    depsgraph = bpy.context.evaluated_depsgraph_get()

    for mesh_object in get_objects('MESH'):
        if mesh_object.data.object_type != 'MESH':
            continue    

        mesh_struct = W3DMesh()
        mesh_struct.header = MeshHeader(
            mesh_name=mesh_object.name,
            container_name=container_name)

        header = mesh_struct.header
        header.sort_level = mesh_object.data.sort_level
        mesh_struct.user_text = mesh_object.data.userText

        if mesh_object.hide_get():
            header.attrs |= GEOMETRY_TYPE_HIDDEN

        if mesh_object.data.casts_shadow:
            header.attrs |= GEOMETRY_TYPE_CAST_SHADOW

        if mesh_object.data.two_sided:
            header.attrs |= GEOMETRY_TYPE_TWO_SIDED

        mesh_object = mesh_object.evaluated_get(depsgraph)
        mesh = mesh_object.data
        b_mesh = prepare_bmesh(context, mesh)
        normal_bk = [Vector] * len(b_mesh.verts)
        for i,v in enumerate(b_mesh.verts):
            # must backup this "old" normal before b_mesh.to_mesh() ruins it
            # use old normal for export
            normal_bk[i] = v.normal 
        b_mesh.to_mesh(mesh)
        mesh.update()


        if len(mesh.vertices) == 0:
            context.warning(f'mesh \'{mesh.name}\' does not have a single vertex!')
            continue

        center, radius = calculate_mesh_sphere(mesh)
        header.sph_center = center
        header.sph_radius = radius

        if mesh.uv_layers:
            mesh.calc_tangents()

        header.vert_count = len(mesh.vertices)

        loop_dict = dict()
        for loop in mesh.loops:
            loop_dict[loop.vertex_index] = loop

        _, _, scale = mesh_object.matrix_local.decompose()

        is_skinned = False
        for vertex in mesh.vertices:
            if vertex.groups:
                is_skinned = True

        unskinned_vertices_error = False
        overskinned_vertices_error = False

        for i, vertex in enumerate(mesh.vertices):
            mesh_struct.shade_ids.append(i)
            matrix = Matrix.Identity(4)
            matrix_2 = Matrix.Identity(4)

            if vertex.groups and hierarchy:
                vert_inf = VertexInfluence()
                vert_inf.bone_idx = find_bone_index(hierarchy, mesh_object, vertex.groups[0].group)
                vert_inf.bone_inf = vertex.groups[0].weight

                # add extra influenced bones
                if len(vertex.groups) > 1:
                    mesh_struct.multi_bone_skinned = True
                    vert_inf.xtra_idx = find_bone_index(hierarchy, mesh_object, vertex.groups[1].group)
                    vert_inf.xtra_inf = vertex.groups[1].weight
                if len(vertex.groups) > 2:
                    overskinned_vertices_error = True
                    context.error(
                        f'mesh \'{mesh_object.name}\' vertex {i} is influenced by more than 2 bones ({len(vertex.groups)})! Make sure you do weight painting on vertex basis not per face.')

                if vert_inf.bone_inf < 0.01 and vert_inf.xtra_inf < 0.01:
                    context.warning(f'mesh \'{mesh_object.name}\' vertex {i} both bone weights where 0!')
                    vert_inf.bone_inf = 1.0
                    vert_inf.xtra_inf = 0.0

                if abs(vert_inf.bone_inf + vert_inf.xtra_inf - 1.0) > 0.1:
                    context.warning(
                        f'mesh \'{mesh_object.name}\' vertex {i} both bone weights did not add up to 100%! ({vert_inf.bone_inf:.{2}f}, {vert_inf.xtra_inf:.{2}f}). Will be normalized!')
                    _bone_inf = vert_inf.bone_inf / (vert_inf.xtra_inf + vert_inf.bone_inf)
                    _xtra_inf = vert_inf.xtra_inf / (vert_inf.xtra_inf + vert_inf.bone_inf)
                    vert_inf.bone_inf = _bone_inf
                    vert_inf.xtra_inf = _xtra_inf

                mesh_struct.vert_infs.append(vert_inf)

                if vert_inf.bone_idx > 0:
                    matrix = matrix @ rig.data.bones[hierarchy.pivots[vert_inf.bone_idx].name].matrix_local.inverted()
                else:
                    matrix = matrix @ rig.matrix_local.inverted()

                if vert_inf.xtra_inf > 0:
                    if vert_inf.xtra_idx > 0:
                        matrix_2 = matrix_2 @ rig.data.bones[hierarchy.pivots[vert_inf.xtra_idx].name].matrix_local.inverted()
                    else:
                        matrix_2 = matrix_2 @ rig.matrix_local.inverted()
                else:
                    matrix_2 = matrix

            elif is_skinned and hierarchy:
                unskinned_vertices_error = True
                context.error(f'skinned mesh \'{mesh_object.name}\' vertex {i} is not rigged to any bone!')

            translation_self = mesh_object.matrix_local
            _, rotation_self, _ = translation_self.decompose()
            _, rotation, _ = matrix.decompose()
            _, rotation_2, _ = matrix_2.decompose()

            # compute coordinates
            mesh_struct.verts.append(matrix @ translation_self @ vertex.co)
            mesh_struct.verts_2.append(matrix_2 @ translation_self @ vertex.co)

            if i in loop_dict:
                loop = loop_dict[i]
                # do NOT use loop.normal here! that might result in weird shading issues
                mesh_struct.normals.append(rotation @ rotation_self @ normal_bk[i])
                mesh_struct.normals_2.append(rotation_2 @ rotation_self @ normal_bk[i])

                if mesh.uv_layers:
                    # in order to adapt to 3ds max orientation
                    mesh_struct.tangents.append((rotation @ rotation_self @ loop.bitangent) * -1)
                    mesh_struct.bitangents.append((rotation @ rotation_self @ loop.tangent))
            else:
                context.warning(f'mesh \'{mesh_object.name}\' vertex {i} is not connected to any face!')
                mesh_struct.normals.append(rotation @ rotation_self @ vertex.normal)
                mesh_struct.normals_2.append(rotation_2 @ rotation_self @ vertex.normal)

                if mesh.uv_layers:
                    # only dummys
                    mesh_struct.tangents.append((rotation @ rotation_self @ vertex.normal) * -1)
                    mesh_struct.bitangents.append((rotation @ rotation_self @ vertex.normal))

        if unskinned_vertices_error or overskinned_vertices_error:
            return ([], [])

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

        if bpy.app.version < (4, 0, 0):
            face_maps = mesh_object.face_maps
        else:
            face_maps = mesh.face_maps

        if context.file_format == 'W3X' and len(face_maps) > 0:
            context.warning('triangle surface types (mesh face maps) are not supported in W3X file format!')
        else:
            face_map_names = [map.name for map in face_maps]
            Triangle.validate_face_map_names(context, face_map_names)

            if bpy.app.version < (4, 0, 0):
                for map in mesh.face_maps:
                    for i, val in enumerate(map.data):
                        mesh_struct.triangles[i].set_surface_type(face_map_names[val.value])
            else:
                for map in mesh.face_maps:
                    for val in map.value:
                        if val.value < len(mesh_struct.triangles):
                            mesh_struct.triangles[val.value].set_surface_type(map.name)

        header.face_count = len(mesh_struct.triangles)

        center, radius = calculate_mesh_sphere(mesh)
        header.sphCenter = center
        header.sphRadius = radius

        tx_stages = []
        for i, uv_layer in enumerate(mesh.uv_layers):
            stage = TextureStage(
                tx_ids=[[i]],
                tx_coords=[[Vector((0.0, 0.0))] * len(mesh_struct.verts)])

            for j, face in enumerate(b_mesh.faces):
                for loop in face.loops:
                    vert_index = mesh_struct.triangles[j].vert_ids[loop.index % 3]
                    stage.tx_coords[0][vert_index] = uv_layer.data[loop.index].uv.copy()
            tx_stages.append(stage)

        b_mesh.free()

        for i, material in enumerate(mesh.materials):
            mat_pass = MaterialPass()

            if material is None:
                context.warning(f'mesh \'{mesh_object.name}\' uses a invalid/empty material!')
                continue

            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)

            if context.file_format == 'W3X' or (
                    material.material_type == 'SHADER_MATERIAL' and not force_vertex_materials):
                mat_pass.shader_material_ids = [i]
                if i < len(tx_stages):
                    mat_pass.tx_coords = tx_stages[i].tx_coords[0]
                # FIX ME: ugly solution to export second uv map!
                # How to deal with multiple materials aganist multiple UV maps in a mesh?
                if len(mesh.materials) == 1 and len(tx_stages) == 2:
                    mat_pass.tx_coords_2 = tx_stages[i + 1].tx_coords[0]

                mesh_struct.shader_materials.append(
                    retrieve_shader_material(context, material, principled))

            else:
                shader = retrieve_shader(material)
                mesh_struct.shaders.append(shader)
                mat_pass.shader_ids = [i]
                mat_pass.vertex_material_ids = [i]

                mesh_struct.vert_materials.append(retrieve_vertex_material(material, principled))

                base_col_tex = principled.base_color_texture
                if base_col_tex is not None and base_col_tex.image is not None:
                    info = TextureInfo()
                    img = base_col_tex.image
                    filepath = os.path.basename(img.filepath)
                    if filepath == '':
                        filepath = img.name
                    tex = Texture(
                        id=img.name,
                        file=filepath,
                        texture_info=info)
                    mesh_struct.textures.append(tex)
                    shader.texturing = 1

                    if i < len(tx_stages):
                        mat_pass.tx_stages.append(tx_stages[i])

            mesh_struct.material_passes.append(mat_pass)

        for layer in mesh.vertex_colors:
            if '_' in layer.name:
                index = int(layer.name.split('_')[-1])
            else:
                index = 0
            if 'DCG' in layer.name:
                target = mesh_struct.material_passes[index].dcg
            elif 'DIG' in layer.name:
                target = mesh_struct.material_passes[index].dig
            elif 'SCG' in layer.name:
                target = mesh_struct.material_passes[index].scg
            else:
                context.warning(f'vertex color layer name \'{layer.name}\' is not one of [DCG, DIG, SCG]')
                continue

            target[:] = [RGBA()] * len(mesh.vertices)

            for i, loop in enumerate(mesh.loops):
                target[loop.vertex_index] = RGBA(layer.data[i].color)

        header.vert_channel_flags = VERTEX_CHANNEL_LOCATION | VERTEX_CHANNEL_NORMAL

        if mesh_struct.vert_infs:
            header.attrs |= GEOMETRY_TYPE_SKIN
            header.vert_channel_flags |= VERTEX_CHANNEL_BONE_ID

            if len(mesh_object.constraints) > 0:
                context.warning(f'mesh \'{mesh_object.name }\' is rigged and thus does not support any constraints!')

        else:
            if len(mesh_object.constraints) > 1:
                context.warning(
                    f'mesh \'{mesh_object.name}\' has multiple constraints applied, only \'Copy Rotation\' OR \'Damped Track\' are supported!')
            for constraint in mesh_object.constraints:
                if constraint.name == 'Copy Rotation':
                    header.attrs |= GEOMETRY_TYPE_CAMERA_ORIENTED
                    break
                if constraint.name == 'Damped Track':
                    header.attrs |= GEOMETRY_TYPE_CAMERA_ALIGNED
                    break
                context.warning(f'mesh \'{mesh_object.name}\' constraint \'{constraint.name}\' is not supported!')

        if mesh_object.name in bone_names:
            if not (mesh_struct.is_skin() or mesh_object.parent_type ==
                    'BONE' and mesh_object.parent_bone == mesh_object.name):
                naming_error = True
                context.error(
                    f'mesh \'{mesh_object.name}\' has same name as bone \'{mesh_object.name}\' but is not configured properly!')
                context.info('EITHER apply an armature modifier to it, create a vertex group with the same name as the mesh and do the weight painting OR set the armature as parent object and the identically named bone as parent bone.')
                continue

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

    if naming_error:
        return [], []

    return mesh_structs


##########################################################################
# Helper methods
##########################################################################


def prepare_bmesh(context, mesh: Mesh):
    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)
    bmesh.ops.triangulate(b_mesh, faces=b_mesh.faces)
    b_mesh.to_mesh(mesh)
    mesh.update()

    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)
    b_mesh = split_multi_uv_vertices(context, b_mesh)
    
    return b_mesh


def find_bone_index(hierarchy, mesh_object, group):
    indices = [i for i, pivot in enumerate(hierarchy.pivots) if pivot.name.lower()
               == mesh_object.vertex_groups[group].name.lower()]
    if indices:
        return indices[0]
    raise Exception(f'no matching armature bone found for vertex group \'{mesh_object.vertex_groups[group].name}\'')


def split_multi_uv_vertices(context, b_mesh: bmesh.types.BMesh):
    uv_layers = [layer for layer in b_mesh.loops.layers.uv.values()]
    deform_layer = b_mesh.verts.layers.deform.active

    if not uv_layers:
        return b_mesh

    split_vert_count = 0 

    for v in list(b_mesh.verts):
        linked_faces = [f for f in v.link_faces]
        if len(linked_faces) <= 1:
            continue

        original_normal = v.normal.copy()

        uv_signatures = {}
        for face in linked_faces:
            loop = next((l for l in face.loops if l.vert == v), None)
            if not loop:
                continue

            signature = tuple((loop[layer].uv.x, loop[layer].uv.y) for layer in uv_layers)
            uv_signatures.setdefault(signature, []).append(face)

        if len(uv_signatures) <= 1:
            continue

        first = True
        for signature, faces in uv_signatures.items():
            if first:
                first = False
                continue

            new_vert = b_mesh.verts.new(v.co)
            new_vert.normal = original_normal
            new_vert.select_set(True)
            split_vert_count += 1

            if deform_layer:
                v_deform = v[deform_layer]
                new_vert_deform = new_vert[deform_layer]
                for group, weight in v_deform.items():
                    new_vert_deform[group] = weight

            for face in faces:
                old_verts = [loop.vert for loop in face.loops]
                new_verts = [
                    new_vert if loop.vert == v else loop.vert
                    for loop in face.loops
                ]

                uv_data = {}
                for layer in uv_layers:
                    uv_data[layer] = [loop[layer].uv.copy() for loop in face.loops]
                face_normal = face.normal

                b_mesh.faces.remove(face)

                new_face = b_mesh.faces.new(new_verts)
                new_face.normal = face_normal
                
                for loop, old_uvs in zip(new_face.loops, zip(*[uv_data[layer] for layer in uv_layers])):
                    for layer, uv in zip(uv_layers, old_uvs):
                        loop[layer].uv = uv

                for loop in new_face.loops:
                    if loop.vert == new_vert:
                        loop.vert.normal = original_normal

    if split_vert_count > 0:
        context.info(f"Split {split_vert_count} vertices with multiple uv coordinates on it")
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
