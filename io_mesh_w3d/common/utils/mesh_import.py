# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.common.utils.material_import import *


def create_mesh(context, mesh_struct, coll):
    triangles = []
    for triangle in mesh_struct.triangles:
        triangles.append(tuple(triangle.vert_ids))

    mesh = bpy.data.meshes.new(mesh_struct.name())

    mesh.from_pydata(mesh_struct.verts, [], triangles)
    mesh.update()
    mesh.validate()

    mesh_ob = bpy.data.objects.new(mesh_struct.name(), mesh)
    mesh_ob.object_type = 'NORMAL'
    mesh_ob.userText = mesh_struct.user_text
    mesh_ob.use_empty_image_alpha = True

    smooth_mesh(mesh_ob, mesh)
    link_object_to_active_scene(mesh_ob, coll)

    if mesh_struct.is_hidden():
        mesh_ob.hide_set(True)

    principleds = []

    # vertex material stuff
    name = mesh_struct.name()
    if mesh_struct.vert_materials:
        create_vertex_material(context, principleds, mesh_struct, mesh, name, triangles)

    for i, shader in enumerate(mesh_struct.shaders):
        set_shader_properties(mesh.materials[i], shader)

    # shader material stuff
    if mesh_struct.shader_materials:
        for i, shaderMat in enumerate(mesh_struct.shader_materials):
            (material, principled) = create_material_from_shader_material(
                context, mesh_struct.name(), shaderMat)
            mesh.materials.append(material)
            principleds.append(principled)

        if mesh_struct.material_passes:
            b_mesh = bmesh.new()
            b_mesh.from_mesh(mesh)

        for mat_pass in mesh_struct.material_passes:
            create_uvlayer(context, mesh, b_mesh, triangles, mat_pass)


def rig_mesh(mesh_struct, hierarchy, rig, sub_object=None):
    mesh_ob = bpy.data.objects[mesh_struct.name()]

    if hierarchy is None or not hierarchy.pivots:
        return

    if mesh_struct.is_skin():
        mesh = bpy.data.meshes[mesh_ob.name]
        for i, vert_inf in enumerate(mesh_struct.vert_infs):
            weight = vert_inf.bone_inf
            if weight < 0.01:
                weight = 1.0

            pivot = hierarchy.pivots[vert_inf.bone_idx]
            if vert_inf.bone_idx <= 0:
                bone = rig
            else:
                bone = rig.data.bones[pivot.name]
            mesh.vertices[i].co = bone.matrix_local @ mesh.vertices[i].co

            if pivot.name not in mesh_ob.vertex_groups:
                mesh_ob.vertex_groups.new(name=pivot.name)
            mesh_ob.vertex_groups[pivot.name].add(
                [i], weight, 'REPLACE')

            if vert_inf.xtra_idx > 0:
                xtra_pivot = hierarchy.pivots[vert_inf.xtra_idx]
                if xtra_pivot.name not in mesh_ob.vertex_groups:
                    mesh_ob.vertex_groups.new(name=xtra_pivot.name)
                mesh_ob.vertex_groups[xtra_pivot.name].add(
                    [i], vert_inf.xtra_inf, 'ADD')

        modifier = mesh_ob.modifiers.new(rig.name, 'ARMATURE')
        modifier.object = rig
        modifier.use_bone_envelopes = False
        modifier.use_vertex_groups = True

    else:
        rig_object(mesh_ob, hierarchy, rig, sub_object)


def smooth_mesh(mesh_ob, mesh):
    if mesh_ob.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for polygon in mesh.polygons:
        polygon.use_smooth = True
