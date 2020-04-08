# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3d.structs.mesh_structs.shader import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *


def retrieve_material(context, material):
    vertex_materials_ids = [VertexMaterialGroup.name, PrelitUnlitGroup.name, PrelitVertexGroup.name,
                    PrelitLightmapMultiPassGroup.name, PrelitLightmapMultiTextureGroup.name]

    shader_node = get_shader_node_group(context, material.node_tree)

    if shader_node.node_tree.name in vertex_materials_ids:
        retrieve_vertex_material(context, material, shader_node)
    # else: shader material


def retrieve_vertex_material(context, material, shader_node):
    node_tree = material.node_tree

    info = VertexMaterialInfo(
        attributes=0,
        shininess=material.specular_intensity,
        specular=get_color_value(context, node_tree, shader_node, 'Specular'),
        diffuse=get_color_value(context, node_tree, shader_node, 'Diffuse'),
        emissive=get_color_value(context, node_tree, shader_node, 'Emissive'),
        ambient=get_color_value(context, node_tree, shader_node, 'Ambient'),
        translucency=get_value(context, node_tree, shader_node, 'Translucency', float),
        opacity=get_value(context, node_tree, shader_node, 'Opacity', float))

    if 'USE_DEPTH_CUE' in material.attributes:
        info.attributes |= USE_DEPTH_CUE
    if 'ARGB_EMISSIVE_ONLY' in material.attributes:
        info.attributes |= ARGB_EMISSIVE_ONLY
    if 'COPY_SPECULAR_TO_DIFFUSE' in material.attributes:
        info.attributes |= COPY_SPECULAR_TO_DIFFUSE
    if 'DEPTH_CUE_TO_ALPHA' in material.attributes:
        info.attributes |= DEPTH_CUE_TO_ALPHA

    vert_mat = VertexMaterial()
    vert_mat.vm_name = shader_node.label
    vert_mat.vm_info = info
    # TODO: handle these
    vert_mat.vm_args_0 = material.vm_args_0
    vert_mat.vm_args_1 = material.vm_args_1

    shader = Shader(
        depth_compare=get_value(context, node_tree, shader_node, 'DepthCompare', int),
        depth_mask=get_value(context, node_tree, shader_node, 'DepthMask', int),
        color_mask=get_value(context, node_tree, shader_node, 'ColorMask', int),
        dest_blend=get_value(context, node_tree, shader_node, 'DestBlend', int),
        fog_func=get_value(context, node_tree, shader_node, 'FogFunc', int),
        pri_gradient=get_value(context, node_tree, shader_node, 'PriGradient', int),
        sec_gradient=get_value(context, node_tree, shader_node, 'SecGradient', int),
        src_blend=get_value(context, node_tree, shader_node, 'SrcBlend', int),
        texturing=get_value(context, node_tree, shader_node, 'Texturing', int), #TODO: set this based on applied texture?
        detail_color_func=get_value(context, node_tree, shader_node, 'DetailColorFunc', int),
        detail_alpha_func=get_value(context, node_tree, shader_node, 'DetailAlphaFunc', int),
        shader_preset=get_value(context, node_tree, shader_node, 'Preset', int),
        alpha_test=get_value(context, node_tree, shader_node, 'AlphaTest', int),
        post_detail_color_func=get_value(context, node_tree, shader_node, 'PostDetailColorFunc', int),
        post_detail_alpha_func=get_value(context, node_tree, shader_node, 'PostDetailAlphaFunc', int))

    (texture, uv_map) = get_texture_value(context, node_tree, shader_node, 'DiffuseTexture')

    return (vert_mat, shader, texture, uv_map)


def retrieve_shader_material(context, material, shader_node):
    name = shader_node.node_tree.name
    shader_mat = ShaderMaterial(
        header=ShaderMaterialHeader(
            type_name=name),
        properties=[])

    shader_mat.header.technique_index = material.technique

    filename = name.replace('.fx', '.xml')
    input_types_dict = get_group_input_types(filename)
    node_tree = material.node_tree

    uv_map = None

    for input in shader_node.inputs:
        if input.identifier in input_types_dict:
            (type, default) = input_types_dict[input.identifier]
            if type == 'ShaderNodeTexture':
                (texture, uv_map) = get_texture_value(context, node_tree, input)
                if texture is not None:
                    shader_mat.properties.append(ShaderMaterialProperty(
                        type=STRING_PROPERTY,
                        name=input.identifier,
                        value=texture))

            elif type == 'ShaderNodeFloat':
                value = get_value(context, node_tree, input)
                default = child_node.get('default', 0.0)
            elif type == 'ShaderNodeVector2':
                default = child_node.get('default', Vector((0.0, 0.0)))
            elif type == 'ShaderNodeVector':
                default = child_node.get('default', Vector((0.0, 0.0, 0.0)))
            elif type == 'ShaderNodeVector4':
                default = child_node.get('default', Vector((0.0, 0.0, 0.0, 0.0)))
            elif type == 'ShaderNodeInt':
                default = child_node.get('default', 0)
            elif type == 'ShaderNodeByte':
                default = child_node.get('default', 0)
            append_property(shader_mat, type, input.identifier, input.)
        else:
            context.warning('node group input ' + input.identifier + ' is not defined in ' + filename)

    return shader_mat

