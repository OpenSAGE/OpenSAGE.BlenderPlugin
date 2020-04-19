# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.shading.vertex_material_group import *
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *


def create_uv_layer(mesh, b_mesh, triangles, tx_coords):
    if tx_coords is None:
        return

    uv_layer = mesh.uv_layers.new(do_init=False)
    for i, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            idx = triangles[i][loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx].xy


class Pipeline():
    vert_mat_id = None
    shader_id = None
    texture_id = None
    shader_mat_id = None
    uv_coords = None


def expand(ids, count):
    if len(ids) != count:
        return [ids[0]] * count
    return ids


def create_materials(context, mesh_struct, mesh, triangles):
    num_faces = len(triangles)
    face_pipelines = [[]] * num_faces

    for mat_pass in mesh_struct.material_passes:
        vert_mat_ids = [None] * num_faces
        shader_ids = [None] * num_faces
        texture_ids = [None] * num_faces
        shader_mat_ids = [None] * num_faces
        uv_coords = None

        if mat_pass.vertex_material_ids:
            vert_mat_ids = expand(mat_pass.vertex_material_ids, num_faces)

        if mat_pass.shader_ids:
            shader_ids = expand(mat_pass.shader_ids, num_faces)

        if mat_pass.shader_material_ids:
            shader_mat_ids = expand(mat_pass.shader_material_ids, num_faces)

        if mat_pass.tx_coords:
            uv_coords = mat_pass.tx_coords

        # TODO: do the tx stages stuff
        #for tx_stage in mat_pass.tx_stages:





def create_material_pass(context, base_struct, mesh, triangles):
    vert_material = None
    shader = None
    texture = None
    tx_coords = None

    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)
    mat_pass = base_struct.material_passes[0]

    if mat_pass.vertex_material_ids:
        vert_material = base_struct.vert_materials[mat_pass.vertex_material_ids[0]]

    if mat_pass.shader_ids:
        shader = base_struct.shaders[mat_pass.shader_ids[0]]

    if mat_pass.tx_stages:
        tx_stage = mat_pass.tx_stages[0]
        texture = base_struct.textures[tx_stage.tx_ids[0]]
        tx_coords = tx_stage.tx_coords

    if vert_material is not None and shader is not None:
        create_vertex_material(context, mesh, b_mesh, triangles, vert_material, shader, texture, tx_coords)

    if mat_pass.shader_material_ids:
        shader_material = base_struct.shader_materials[0]
        create_shader_material(context, mesh, b_mesh, triangles, shader_material, mat_pass.tx_coords)

    b_mesh.free()


##########################################################################
# vertex material
##########################################################################

def create_vertex_material(context, mesh, b_mesh, triangles, vert_mat, shader, texture_struct, tx_coords):
    material = bpy.data.materials.new(mesh.name + '.' + vert_mat.vm_name)
    mesh.materials.append(material)

    create_uv_layer(mesh, b_mesh, triangles, tx_coords)

    material.use_nodes = True
    material.shadow_method = 'CLIP'
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    node_tree = material.node_tree
    links = node_tree.links

    node_tree.nodes.remove(node_tree.nodes.get('Principled BSDF'))

    instance = VertexMaterialGroup.create(node_tree, vert_mat, shader)
    instance.label = vert_mat.vm_name
    instance.location = (0, 300)
    instance.width = 200

    output = node_tree.nodes.get('Material Output')
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])

    if texture_struct is not None:
        texture = find_texture(context, texture_struct.file, texture_struct.id)

        texture_node = node_tree.nodes.new('ShaderNodeTexImage')
        texture_node.image = texture
        texture_node.location = (-350, 300)
        links.new(texture_node.outputs['Color'], instance.inputs['DiffuseTexture'])
        links.new(texture_node.outputs['Alpha'], instance.inputs['DiffuseTextureAlpha'])


##########################################################################
# shader material
##########################################################################


def create_shader_material(context, mesh, b_mesh, triangles, shader_mat, tx_coords):
    mat_name = shader_mat.header.type_name
    create_uv_layer(mesh, b_mesh, triangles, tx_coords)

    if mat_name in bpy.data.materials:
        mesh.materials.append(bpy.data.materials[mat_name])
        return

    material = bpy.data.materials.new(mat_name)
    mesh.materials.append(material)
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    node_tree = material.node_tree
    node_tree.nodes.remove(node_tree.nodes.get('Principled BSDF'))

    instance = node_tree.nodes.new(type='ShaderNodeGroup')
    instance.node_tree = bpy.data.node_groups[mat_name]
    instance.label = mat_name
    instance.location = (0, 300)
    instance.width = 200

    links = node_tree.links

    if shader_mat.header.technique is not None:
        instance.inputs['Technique'].default_value = shader_mat.header.technique

    y = 300
    for prop in shader_mat.properties:
        if prop.type == STRING_PROPERTY and prop.value != '':
            texture_node = node_tree.nodes.new('ShaderNodeTexImage')
            texture_node.image = find_texture(context, prop.value)
            texture_node.location = (-350, y)
            y -= 300

            links.new(texture_node.outputs['Color'], instance.inputs[prop.name])
            index = instance.inputs.keys().index(prop.name)
            links.new(texture_node.outputs['Alpha'], instance.inputs[index + 1])

        elif prop.type == VEC4_PROPERTY:
            instance.inputs[prop.name].default_value = prop.to_rgba()
        else:
            instance.inputs[prop.name].default_value = prop.value

    output = node_tree.nodes.get('Material Output')
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])
