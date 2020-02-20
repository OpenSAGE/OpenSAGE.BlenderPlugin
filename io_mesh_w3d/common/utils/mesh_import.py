# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from io_mesh_w3d.common.utils.material_import import *


def create_mesh(context, mesh_struct, coll):
    triangles = []
    for triangle in mesh_struct.triangles:
        triangles.append(tuple(triangle.vert_ids))

    mesh = bpy.data.meshes.new(mesh_struct.name())
    mesh.from_pydata(mesh_struct.verts, [], triangles)

    mesh.normals_split_custom_set_from_vertices(mesh_struct.normals)
    mesh.use_auto_smooth = True

    mesh.update()
    mesh.validate()

    mesh_ob = bpy.data.objects.new(mesh_struct.name(), mesh)
    mesh_ob.object_type = 'NORMAL'
    mesh_ob.userText = mesh_struct.user_text
    mesh_ob.use_empty_image_alpha = True

    link_object_to_active_scene(mesh_ob, coll)

    if mesh_struct.is_hidden():
        mesh_ob.hide_set(True)

    create_material_passes(context, mesh_struct, mesh, triangles)

    # create_shader_materials(context, mesh_struct, mesh, triangles)

    #create_vertex_materials(context, mesh_struct, mesh, triangles)
    #create_vertex_materials(context, mesh_struct.prelit_unlit, mesh, triangles, prelit_type='PRELIT_UNLIT')
    #create_vertex_materials(context, mesh_struct.prelit_vertex, mesh, triangles, prelit_type='PRELIT_VERTEX')
    #create_vertex_materials(context, mesh_struct.prelit_lightmap_multi_pass, mesh, triangles, prelit_type='PRELIT_LIGHTMAP_MULTI_PASS')
    #create_vertex_materials(context, mesh_struct.prelit_lightmap_multi_texture, mesh, triangles, prelit_type='PRELIT_LIGHTMAP_MULTI_TEXTURE')


def rig_mesh(mesh_struct, hierarchy, rig, sub_object=None):
    mesh_ob = bpy.data.objects[mesh_struct.name()]

    if hierarchy is None or not hierarchy.pivots:
        return

    if mesh_struct.is_skin():
        mesh = bpy.data.meshes[mesh_ob.name]
        normals = [None] * len(mesh_struct.normals)
        for i, vert_inf in enumerate(mesh_struct.vert_infs):
            weight = vert_inf.bone_inf
            if weight < 0.01:
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
                mesh_ob.vertex_groups[xtra_pivot.name].add(
                    [i], vert_inf.xtra_inf, 'ADD')

            mesh.vertices[i].co = matrix @ mesh_struct.verts[i]

            (_, rotation, _) = matrix.decompose()
            normals[i] = rotation @ mesh_struct.normals[i]

        modifier = mesh_ob.modifiers.new(rig.name, 'ARMATURE')
        modifier.object = rig
        modifier.use_bone_envelopes = False
        modifier.use_vertex_groups = True

        mesh.normals_split_custom_set_from_vertices(normals)
        mesh.use_auto_smooth = True

        mesh.update()
        mesh.validate()

    else:
        rig_object(mesh_ob, hierarchy, rig, sub_object)