# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.shading.vertex_material_group import VertexMaterialGroup
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *


def create_material(name):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.shadow_method = 'CLIP'
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    node_tree = material.node_tree
    node_tree.nodes.remove(node_tree.nodes.get('Principled BSDF'))

    return material, node_tree


#######################################################################################################################
# vertex material
#######################################################################################################################


def create_vertex_material(context, mesh_struct, uv_layer):
    vert_mat = mesh_struct.vert_materials[0]
    shader = mesh_struct.shaders[0]
    texture = mesh_struct.textures[0]

    material_name = mesh_struct.name() + "." + vert_mat.vm_name

    material, node_tree = create_material(material_name)

    instance = VertexMaterialGroup.create(node_tree, vert_mat, shader)
    instance.label = vert_mat.vm_name
    instance.location = (0, 300)
    instance.width = 200
    instance.hide = True

    output = node_tree.nodes.get('Material Output')

    links = node_tree.links
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])

    # TODO: check for texture and uv coords!
    texture = find_texture(context, texture.file, texture.id)
    texture_node = node_tree.nodes.new('ShaderNodeTexImage')
    texture_node.image = texture
    texture_node.location = (-350, 300)
    texture_node.hide = True

    links.new(texture_node.outputs['Color'], instance.inputs['DiffuseTexture'])
    links.new(texture_node.outputs['Alpha'], instance.inputs['DiffuseTextureAlpha'])

    uv_node = node_tree.nodes.new('ShaderNodeUVMap')
    uv_node.location = (-550, 300)
    uv_node.uv_map = uv_layer

    links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])

    return material


#######################################################################################################################
# shader material
#######################################################################################################################

def create_shader_material(context, shader_material, uv_layer):
    material_name = shader_material.header.type_name

    material, node_tree = create_material(material_name)

    instance = node_tree.nodes.new(type='ShaderNodeGroup')
    instance.node_tree = bpy.data.node_groups[material_name]
    instance.label = material_name
    instance.location = (0, 300)
    instance.width = 200

    links = node_tree.links

    if shader_material.header.technique is not None:
        instance.inputs['Technique'].default_value = shader_material.header.technique

    y = 300
    for prop in shader_material.properties:
        if prop.type == STRING_PROPERTY and prop.value != '':
            texture_node = node_tree.nodes.new('ShaderNodeTexImage')
            texture_node.image = find_texture(context, prop.value)
            texture_node.location = (-350, y)

            links.new(texture_node.outputs['Color'], instance.inputs[prop.name])
            index = instance.inputs.keys().index(prop.name)
            links.new(texture_node.outputs['Alpha'], instance.inputs[index + 1])

            uv_node = node_tree.nodes.new('ShaderNodeUVMap')
            uv_node.location = (-550, y)
            uv_node.uv_map = uv_layer
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
            y -= 300

        elif prop.type == VEC4_PROPERTY:
            instance.inputs[prop.name].default_value = prop.to_rgba()
        else:
            instance.inputs[prop.name].default_value = prop.value

    output = node_tree.nodes.get('Material Output')
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])

    return material


#######################################################################################################################
# set shader properties
#######################################################################################################################


def set_shader_properties(material, shader):
    material.shader.depth_compare = str(shader.depth_compare)
    material.shader.depth_mask = str(shader.depth_mask)
    material.shader.color_mask = shader.color_mask
    material.shader.dest_blend = str(shader.dest_blend)
    material.shader.fog_func = shader.fog_func
    material.shader.pri_gradient = str(shader.pri_gradient)
    material.shader.sec_gradient = str(shader.sec_gradient)
    material.shader.src_blend = str(shader.src_blend)
    material.shader.texturing = str(shader.texturing)
    material.shader.detail_color_func = str(shader.detail_color_func)
    material.shader.detail_alpha_func = str(shader.detail_alpha_func)
    material.shader.shader_preset = shader.shader_preset
    material.shader.alpha_test = str(shader.alpha_test)
    material.shader.post_detail_color_func = str(shader.post_detail_color_func)
    material.shader.post_detail_alpha_func = str(shader.post_detail_alpha_func)


