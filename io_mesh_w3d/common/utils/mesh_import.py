# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from io_mesh_w3d.common.utils.material_import import *


def create_mesh(context, mesh_struct, coll):
    context.info('creating mesh \'' + mesh_struct.name() + '\'')

    triangles = []
    for triangle in mesh_struct.triangles:
        triangles.append(tuple(triangle.vert_ids))

    mesh = bpy.data.meshes.new(mesh_struct.name())
    mesh.from_pydata(mesh_struct.verts, [], triangles)

    mesh.normals_split_custom_set_from_vertices(mesh_struct.normals)
    mesh.use_auto_smooth = True

    mesh.update()
    mesh.validate()

    mesh.object_type = 'MESH'
    mesh.userText = mesh_struct.user_text
    mesh.sort_level = mesh_struct.header.sort_level
    mesh.casts_shadow = mesh_struct.casts_shadow()

    mesh_ob = bpy.data.objects.new(mesh_struct.name(), mesh)

    mesh_ob.use_empty_image_alpha = True

    link_object_to_active_scene(mesh_ob, coll)

    if mesh_struct.is_hidden():
        mesh_ob.hide_set(True)

    if mesh_struct.is_camera_oriented():
        constraint = mesh_ob.constraints.new('COPY_ROTATION')
        constraint.target = bpy.context.scene.camera
        constraint.use_x = False
        constraint.use_y = False
        constraint.use_z = True
        constraint.invert_z = True

    if mesh_struct.is_camera_aligned():
        constraint = mesh_ob.constraints.new('DAMPED_TRACK')
        constraint.target = bpy.context.scene.camera
        constraint.track_axis = 'TRACK_X'

    if context.file_format == 'W3D':
        for i, triangle in enumerate(mesh_struct.triangles):
            surface_type_name = triangle.get_surface_type_name(context, i)
            if surface_type_name not in mesh_ob.face_maps:
                mesh_ob.face_maps.new(name=surface_type_name)

            mesh_ob.face_maps[surface_type_name].add([i])

    for i, mat_pass in enumerate(mesh_struct.material_passes):
        create_vertex_color_layer(mesh, mat_pass.dcg, 'DCG', i)
        create_vertex_color_layer(mesh, mat_pass.dig, 'DIG', i)
        create_vertex_color_layer(mesh, mat_pass.scg, 'SCG', i)

    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    # shader material stuff
    if mesh_struct.shader_materials:
        # TODO: check for no tx coords and more than 1 shader material
        tx_coords = mesh_struct.material_passes[0].tx_coords
        uv_layer = create_uv_layer(mesh, b_mesh, triangles, tx_coords)

        material = create_shader_material(context, mesh_struct.shader_materials[0], uv_layer)
        mesh.materials.append(material)

    # vertex material stuff
    elif mesh_struct.vert_materials:
        # TODO: check for no tx coords and more than 1 vertex material / material pass
        tx_coords = mesh_struct.material_passes[0].tx_stages[0].tx_coords[0]
        uv_layer = create_uv_layer(mesh, b_mesh, triangles, tx_coords)

        material = create_vertex_material(context, mesh_struct, uv_layer)
        mesh.materials.append(material)



def rig_mesh(mesh_struct, hierarchy, rig, sub_object=None):
    mesh_ob = bpy.data.objects[mesh_struct.name()]

    if hierarchy is None or not hierarchy.pivots:
        return

    if mesh_struct.is_skin():
        mesh = bpy.data.meshes[mesh_ob.name]
        normals = mesh_struct.normals.copy()
        for i, vert_inf in enumerate(mesh_struct.vert_infs):
            weight = vert_inf.bone_inf
            xtra_weight = vert_inf.xtra_inf

            if weight < 0.01 and xtra_weight < 0.01:
                weight = 1.0

            pivot = hierarchy.pivots[vert_inf.bone_idx]
            if vert_inf.bone_idx == 0 and rig is not None:
                matrix = rig.matrix_local
            else:
                matrix = rig.data.bones[pivot.name].matrix_local

            if pivot.name not in mesh_ob.vertex_groups:
                mesh_ob.vertex_groups.new(name=pivot.name)
            mesh_ob.vertex_groups[pivot.name].add([i], weight, 'REPLACE')

            if vert_inf.xtra_idx > 0:
                xtra_pivot = hierarchy.pivots[vert_inf.xtra_idx]
                if xtra_pivot.name not in mesh_ob.vertex_groups:
                    mesh_ob.vertex_groups.new(name=xtra_pivot.name)
                mesh_ob.vertex_groups[xtra_pivot.name].add([i], xtra_weight, 'ADD')

            mesh.vertices[i].co = matrix @ mesh_struct.verts[i]

            _, rotation, _ = matrix.decompose()
            normals[i] = rotation @ mesh_struct.normals[i]

        modifier = mesh_ob.modifiers.new(rig.name, 'ARMATURE')
        modifier.object = rig
        modifier.use_bone_envelopes = False
        modifier.use_vertex_groups = True

        mesh.normals_split_custom_set_from_vertices(normals)

        mesh.update()
        mesh.validate()

    else:
        rig_object(mesh_ob, hierarchy, rig, sub_object)


def create_vertex_color_layer(mesh, colors, name, index):
    if not colors:
        return
    layer = mesh.vertex_colors.new(name=name + '_' + str(index))

    for i, loop in enumerate(mesh.loops):
        layer.data[i].color = colors[loop.vertex_index].to_vector_rgba()
