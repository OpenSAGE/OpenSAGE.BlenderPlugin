# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3d.structs.mesh_structs.shader import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.w3d.structs.mesh_structs.material_pass import *
from io_mesh_w3d.common.structs.mesh_structs.texture import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *


def retrieve_material(context, mesh, material, tx_coords):
    shader_node = get_shader_node_group(context, material.node_tree)

    if shader_node.node_tree.name == VertexMaterialGroup.name:
        (vert_mat, shader, tex_name) = retrieve_vertex_material(context, material, shader_node)
        mesh.vertex_materials = [vert_mat]
        mesh.shaders = [shader]
        mesh.textures = [Texture(file=tex_name, info=None)]

        tx_stage = TextureStage(
            tx_ids=[0],
            tx_coords=tx_coords)

        mesh.material_passes.append(MaterialPass(
            vertex_material_ids=[0],
            shader_ids=[0],
            shader_material_ids=[],
            tx_stages=[tx_stage],
            tx_coords=[]))
    else:
        shader_mat = retrieve_shader_material(context, material, shader_node)
        mesh.shader_materials = [shader_mat]

        mesh.material_passes.append(MaterialPass(
            vertex_material_ids=[],
            shader_ids=[],
            shader_material_ids=[0],
            tx_stages=[],
            tx_coords=tx_coords))


def retrieve_vertex_material(context, material, shader_node):
    node_tree = material.node_tree

    print(get_value(context, node_tree, shader_node.inputs['Translucency'], float))

    info = VertexMaterialInfo(
        attributes=0,
        shininess=material.specular_intensity,
        specular=get_color_value(context, node_tree, shader_node.inputs['Specular']),
        diffuse=get_color_value(context, node_tree, shader_node.inputs['Diffuse']),
        emissive=get_color_value(context, node_tree, shader_node.inputs['Emissive']),
        ambient=get_color_value(context, node_tree, shader_node.inputs['Ambient']),
        translucency=get_value(context, node_tree, shader_node.inputs['Translucency'], float),
        opacity=get_value(context, node_tree, shader_node.inputs['Opacity'], float))

    #if 'USE_DEPTH_CUE' in material.attributes:
    #    info.attributes |= USE_DEPTH_CUE
    #if 'ARGB_EMISSIVE_ONLY' in material.attributes:
    #    info.attributes |= ARGB_EMISSIVE_ONLY
    #if 'COPY_SPECULAR_TO_DIFFUSE' in material.attributes:
    #    info.attributes |= COPY_SPECULAR_TO_DIFFUSE
    #if 'DEPTH_CUE_TO_ALPHA' in material.attributes:
    #    info.attributes |= DEPTH_CUE_TO_ALPHA

    vert_mat = VertexMaterial()
    vert_mat.vm_name = shader_node.label
    vert_mat.vm_info = info
    #vert_mat.vm_args_0 = material.vm_args_0
    #vert_mat.vm_args_1 = material.vm_args_1

    shader = Shader(
        depth_compare=get_value(context, node_tree, shader_node.inputs['DepthCompare'], int),
        depth_mask=get_value(context, node_tree, shader_node.inputs['DepthMask'], int),
        color_mask=get_value(context, node_tree, shader_node.inputs['ColorMask'], int),
        dest_blend=get_value(context, node_tree, shader_node.inputs['DestBlend'], int),
        fog_func=get_value(context, node_tree, shader_node.inputs['FogFunc'], int),
        pri_gradient=get_value(context, node_tree, shader_node.inputs['PriGradient'], int),
        sec_gradient=get_value(context, node_tree, shader_node.inputs['SecGradient'], int),
        src_blend=get_value(context, node_tree, shader_node.inputs['SrcBlend'], int),
        texturing=get_value(context, node_tree, shader_node.inputs['Texturing'], int), #TODO: set this based on applied texture?
        detail_color_func=get_value(context, node_tree, shader_node.inputs['DetailColorFunc'], int),
        detail_alpha_func=get_value(context, node_tree, shader_node.inputs['DetailAlphaFunc'], int),
        shader_preset=get_value(context, node_tree, shader_node.inputs['Preset'], int),
        alpha_test=get_value(context, node_tree, shader_node.inputs['AlphaTest'], int),
        post_detail_color_func=get_value(context, node_tree, shader_node.inputs['PostDetailColorFunc'], int),
        post_detail_alpha_func=get_value(context, node_tree, shader_node.inputs['PostDetailAlphaFunc'], int))

    texture = get_texture_value(context, node_tree, shader_node.inputs['DiffuseTexture'])

    return (vert_mat, shader, texture)


def retrieve_shader_material(context, material, shader_node):
    node_tree = shader_node.node_tree
    name = node_tree.name
    shader_mat = ShaderMaterial(
        header=ShaderMaterialHeader(
            type_name=name),
        properties=[])

    shader_mat.header.technique_index = get_value(context, node_tree, shader_node.inputs['Technique'], int)
    
    filename = name.replace('.fx', '.xml')
    input_types_dict = get_group_input_types(filename)

    uv_map = None

    for input in shader_node.inputs:
        if input.name in input_types_dict:
            (type, default) = input_types_dict[input.name]

            if type == 'NodeSocketTexture':
                prop_type = STRING_PROPERTY
                value = get_texture_value(context, node_tree, input)
            elif type == 'NodeSocketTextureAlpha':
                continue
            elif type == 'NodeSocketFloat':
                prop_type = FLOAT_PROPERTY
                value = get_value(context, node_tree, input, float)
            elif type == 'NodeSocketVector2':
                prop_type = VEC2_PROPERTY
                value = get_vec2_value(context, node_tree, input)
            elif type == 'NodeSocketVector':
                prop_type = VEC3_PROPERTY
                value = get_vec_value(context, node_tree, input)
            elif type in ['NodeSocketVector4', 'NodeSocketColor']:
                prop_type = VEC4_PROPERTY
                value = get_color_value(context, node_tree, input)
            elif type == 'NodeSocketInt':
                prop_type = LONG_PROPERTY
                value = get_value(context, node_tree, input, int)
            elif type == 'NodeSocketByte':
                prop_type = BYTE_PROPERTY
                value = get_value(context, node_tree, input, int)
            else:
                context.warning('Invalid node socket type: ' + type + ' !')
            if value != default:
                shader_mat.properties.append(ShaderMaterialProperty(type=prop_type, name=input.name, value=value))
        else:
            context.warning('node group input ' + input.name + ' is not defined in ' + filename)

    return shader_mat

