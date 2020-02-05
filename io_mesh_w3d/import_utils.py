# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bmesh
import bpy

from io_mesh_w3d.shared.utils.hierarchy_import import *
from io_mesh_w3d.shared.utils.animation_import import *
from io_mesh_w3d.shared.utils.material_import import *
from io_mesh_w3d.shared.utils.box_import import *
from io_mesh_w3d.shared.utils.dazzle_import import *
from io_mesh_w3d.shared.utils.primitives import *



def smooth_mesh(mesh_ob, mesh):
    if mesh_ob.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for polygon in mesh.polygons:
        polygon.use_smooth = True


##########################################################################
# data creation
##########################################################################


def create_data(
        context,
        meshes,
        hlod=None,
        hierarchy=None,
        boxes=[],
        animation=None,
        compressed_animation=None,
        dazzles=[]):
    rig = None
    coll = get_collection(hlod)

    rig = get_or_create_skeleton(hlod, hierarchy, coll)

    if hlod is not None:
        current_coll = coll
        for i, lod_array in enumerate(reversed(hlod.lod_arrays)):
            if i > 0:
                current_coll = get_collection(hlod, '.' + str(i))
                # collection has no hide_set()
                current_coll.hide_viewport = True

            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        create_mesh(context, mesh, hierarchy, current_coll)

                for box in boxes:
                    if box.name() == sub_object.name:
                        create_box(box, hlod, hierarchy, rig, coll)

                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        create_dazzle(context, dazzle, hlod, hierarchy, rig, coll)

        for lod_array in reversed(hlod.lod_arrays):
            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        rig_mesh(mesh, hierarchy, rig, sub_object)
                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        dazzle_object = bpy.data.objects[dazzle.name()]
                        rig_object(dazzle_object, hierarchy, rig, sub_object)

    else:
        for mesh in meshes:
            create_mesh(context, mesh, hierarchy, coll)

    create_animation(context, rig, animation, hierarchy)
    create_animation(context, rig, compressed_animation, hierarchy, compressed=True)


def rig_object(object, hierarchy, rig, sub_object):
    if hierarchy is None or not sub_object or sub_object.bone_index <= 0:
        return

    pivot = hierarchy.pivots[sub_object.bone_index]

    if rig is not None and pivot.name in rig.pose.bones:
        object.parent = rig
        object.parent_bone = pivot.name
        object.parent_type = 'BONE'
        return

    object.rotation_mode = 'QUATERNION'
    object.delta_location = pivot.translation
    object.delta_rotation_quaternion = pivot.rotation

    if pivot.parent_id <= 0:
        return

    parent_pivot = hierarchy.pivots[pivot.parent_id]

    if parent_pivot.name in bpy.data.objects:
        object.parent = bpy.data.objects[parent_pivot.name]
    elif rig is not None and parent_pivot.name in rig.pose.bones:
        object.parent = rig
        object.parent_bone = parent_pivot.name
        object.parent_type = 'BONE'


##########################################################################
# mesh
##########################################################################

def create_mesh(context, mesh_struct, hierarchy, coll):
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


##########################################################################
# create basic meshes
##########################################################################

