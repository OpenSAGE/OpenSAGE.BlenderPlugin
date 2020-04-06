# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.node_groups.vertex_material import *
from io_mesh_w3d.common.node_groups.helpers import *
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *


def get_or_create_uv_layer(mesh, b_mesh, triangles, tx_coords):
    for uv_layer in mesh.uv_layers:
        layer_exists = True
        for i, face in enumerate(b_mesh.faces):
            for loop in face.loops:
                idx = triangles[i][loop.index % 3]
                if uv_layer.data[loop.index].uv != tx_coords[idx].xy:
                    layer_exists = False
        if layer_exists:
            return uv_layer.name

    uv_layer = mesh.uv_layers.new(do_init=False)
    for i, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            idx = triangles[i][loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx].xy
    return uv_layer.name


def create_materials_from_combinations(mesh, vert_mat_ids, shader_ids, tex_ids):
    materials = {}

    if len(vert_mat_ids) == 0:
        vert_mat_ids = [vert_mat_ids[0]] * len(mesh.vertices)
    if len(shader_ids) == 0:
        shader_ids = [shader_ids[0]] * len(mesh.vertices)
    if len(tex_ids) == 0:
        tex_ids = [tex_ids[0]] * len(tex_ids)

    # TODO
    #for i, vertex in enumerate(mesh.vertices):



def create_material_passes(context, base_struct, mesh, triangles):
    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    for pass_index, mat_pass in enumerate(base_struct.material_passes):
        vert_materials = []
        shaders = []
        textures = []
        shader_materials = []
        tx_coords = []

        for vert_mat_id in mat_pass.vertex_material_ids:
            vert_materials.append(base_struct.vert_materials[vert_mat_id])

        for shader_id in mat_pass.shader_ids:
            shaders.append(base_struct.shaders[shader_id])

        for tx_stage in mat_pass.tx_stages:
            textures.append(base_struct.textures[tx_stage.tx_ids[0]])
            tx_coords.append(tx_stage.tx_coords)

        for shader_mat_id in mat_pass.shader_material_ids:
            shader_material = base_struct.shader_materials[shader_mat_id]
            create_shader_material(context, mesh, b_mesh, triangles, shader_material, mat_pass.tx_coords)


        #print('vert: ' + str(len(vert_materials)))
        #print('shaders: ' + str(len(shaders)))
        #print('textures: ' + str(len(textures)))
        #print('shader_materials: ' + str(len(shader_materials)))
        #print('tx_coords: ' + str(len(tx_coords)))

        if vert_materials:
            texture = None
            if textures:
                texture = textures[0]
            tx_coordinates = None
            if tx_coords:
                tx_coordinates = tx_coords[0]

            #TODO: create vert_mat - shader - texture combinations
            # and support different materials for each triangle
            create_vertex_material(context, mesh, b_mesh, triangles, vert_materials[0], shaders[0], texture, tx_coordinates, pass_index)

##########################################################################
# vertex material
##########################################################################

def create_vertex_material(context, mesh, b_mesh, triangles, vert_mat, shader, texture_struct, tx_coords, pass_index):
    material = bpy.data.materials.new(mesh.name + '.' + vert_mat.vm_name)
    mesh.materials.append(material)

    material.use_nodes = True
    material.shadow_method = 'CLIP'
    material.blend_method = 'BLEND'
    material.show_transparent_back = False
    material.pass_index = pass_index

    material.attributes = {'DEFAULT'}
    attributes = vert_mat.vm_info.attributes
    if attributes & USE_DEPTH_CUE:
        material.attributes.add('USE_DEPTH_CUE')
    if attributes & ARGB_EMISSIVE_ONLY:
        material.attributes.add('ARGB_EMISSIVE_ONLY')
    if attributes & COPY_SPECULAR_TO_DIFFUSE:
        material.attributes.add('COPY_SPECULAR_TO_DIFFUSE')
    if attributes & DEPTH_CUE_TO_ALPHA:
        material.attributes.add('DEPTH_CUE_TO_ALPHA')

    # TODO: translate those to shader properties
    material.vm_args_0 = vert_mat.vm_args_0
    material.vm_args_1 = vert_mat.vm_args_1

    node_tree = material.node_tree
    links = node_tree.links

    node_tree.nodes.remove(node_tree.nodes.get('Principled BSDF'))

    instance = VertexMaterialGroup.create(node_tree, vert_mat.vm_name, vert_mat.vm_info, shader)
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
        links.new(texture_node.outputs['Color'], instance.inputs['Diffuse'])
        links.new(texture_node.outputs['Alpha'], instance.inputs['DiffuseAlpha'])

        uv_layer = get_or_create_uv_layer(mesh, b_mesh, triangles, tx_coords)

        uv_node = node_tree.nodes.new('ShaderNodeUVMap')
        uv_node.uv_map = uv_layer
        uv_node.location = (-550, 300)
        links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])


##########################################################################
# shader material
##########################################################################


def create_shader_material(context, mesh, b_mesh, triangles, shader_mat, tx_coords):
    mat_name = shader_mat.header.type_name

    # TODO: verify that
    if mat_name in bpy.data.materials:
        mesh.materials.append(bpy.data.materials[mat_name])
        return

    material = bpy.data.materials.new(mat_name)
    mesh.materials.append(material)
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    node_tree = material.node_tree
    links = node_tree.links

    node_tree.nodes.remove(node_tree.nodes.get('Principled BSDF'))

    uv_layer = get_or_create_uv_layer(mesh, b_mesh, triangles, tx_coords)

    instance = node_tree.nodes.new(type='ShaderNodeGroup')
    instance.node_tree = bpy.data.node_groups[mat_name]
    instance.label = mat_name
    instance.location = (0, 300)
    instance.width = 200

    links = node_tree.links

    if shader_mat.header.technique is not None:
        instance.inputs['Technique'].default_value = shader_mat.header.technique

    uv_node = None
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

            if uv_node is None:
                uv_node = node_tree.nodes.new('ShaderNodeUVMap')
                uv_node.uv_map = uv_layer
                uv_node.location = (-600, 300)
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
        elif prop.type == VEC4_PROPERTY:
            instance.inputs[prop.name].default_value = prop.to_rgba()
        else:
            instance.inputs[prop.name].default_value = prop.value

    output = node_tree.nodes.get('Material Output')
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])
