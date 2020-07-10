# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.common.shading.vertex_material_group import *
from io_mesh_w3d.common.structs.mesh_structs.texture import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *
from io_mesh_w3d.w3d.structs.mesh_structs.material_pass import *
from io_mesh_w3d.w3d.structs.mesh_structs.shader import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *

from io_mesh_w3d.common.shading.node_socket_texture import NodeSocketTexture
from io_mesh_w3d.common.shading.node_socket_texture_alpha import NodeSocketTextureAlpha
from io_mesh_w3d.common.shading.node_socket_vec2 import NodeSocketVector2
from io_mesh_w3d.common.shading.node_socket_vec4 import NodeSocketVector4
from bpy.types import NodeSocketFloat, NodeSocketInt, NodeSocketBool, NodeSocketVector, NodeSocketColor


def get_uv_coords(mesh_struct, b_mesh, mesh, uv_layer_name):
    tx_coords = [Vector((0.0, 0.0))] * len(mesh.vertices)

    uv_layer = mesh.uv_layers[uv_layer_name]
    for j, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            vert_index = mesh_struct.triangles[j].vert_ids[loop.index % 3]
            tx_coords[vert_index] = uv_layer.data[loop.index].uv.copy()
    return tx_coords


def retrieve_materials(context, mesh_struct, b_mesh, mesh):
    material = mesh.materials[0]
    shader_node = get_shader_node_group(context, material.node_tree)

    # TODO: check for context.file_format == W3X
    # -> only export shader materials so convert VertexMaterial to DefaultW3D

    if shader_node.node_tree.name == 'VertexMaterial':
        vert_mat, shader, tex_name, uv_layer_name = retrieve_vertex_material(context, material, shader_node)
        mesh_struct.vert_materials = [vert_mat]
        mesh_struct.shaders = [shader]
        mesh_struct.textures = [Texture(file=tex_name)]

        tx_stage = TextureStage(
                tx_ids=[[0]],
                tx_coords=[get_uv_coords(mesh_struct, b_mesh, mesh, uv_layer_name)])

        mesh_struct.material_passes.append(MaterialPass(
            vertex_material_ids=[0],
            shader_ids=[0],
            tx_stages=[tx_stage]))

    else:
        if len(mesh.materials) > 1:
            context.warning('only 1 material supported for shader material export')

        if len(mesh.uv_layers) > 1:
            context.warning('only 1 uv_layer supported for shader material export')

        shader_mat = retrieve_shader_material(context, material, shader_node)
        mesh_struct.shader_materials = [shader_mat]

        mesh_struct.material_passes.append(MaterialPass(
            shader_material_ids=[0],
            tx_coords=get_uv_coords(mesh_struct, b_mesh, mesh, mesh.uv_layers[0].name)))


def retrieve_vertex_material(context, material, shader_node):
    node_tree = material.node_tree

    info = VertexMaterialInfo(
        attributes=0,
        diffuse=get_color_value(context, node_tree, shader_node.inputs['Diffuse']),
        ambient=get_color_value(context, node_tree, shader_node.inputs['Ambient']),
        specular=get_color_value(context, node_tree, shader_node.inputs['Specular']),
        emissive=get_color_value(context, node_tree, shader_node.inputs['Emissive']),
        shininess=get_value(context, node_tree, shader_node.inputs['Shininess'], float),
        opacity=get_value(context, node_tree, shader_node.inputs['Opacity'], float),
        translucency=get_value(context, node_tree, shader_node.inputs['Translucency'], float))


    node_attributes = shader_node.inputs['Attributes'].default_value
    if 'USE_DEPTH_CUE' in node_attributes:
        info.attributes |= USE_DEPTH_CUE
    if 'ARGB_EMISSIVE_ONLY' in node_attributes:
        info.attributes |= ARGB_EMISSIVE_ONLY
    if 'COPY_SPECULAR_TO_DIFFUSE' in node_attributes:
        info.attributes |= COPY_SPECULAR_TO_DIFFUSE
    if 'DEPTH_CUE_TO_ALPHA' in node_attributes:
        info.attributes |= DEPTH_CUE_TO_ALPHA


    vert_mat = VertexMaterial()
    vert_mat.vm_name = shader_node.label
    vert_mat.vm_info = info
    vert_mat.vm_args_0 = shader_node.inputs['VM_ARGS_0'].default_value
    vert_mat.vm_args_1 = shader_node.inputs['VM_ARGS_1'].default_value

    shader = Shader(
        depth_compare=get_value(context, node_tree, shader_node.inputs['DepthCompare'], int),
        depth_mask=get_value(context, node_tree, shader_node.inputs['DepthMaskWrite'], int),
        color_mask=get_value(context, node_tree, shader_node.inputs['ColorMask'], int),
        fog_func=get_value(context, node_tree, shader_node.inputs['FogFunc'], int),
        dest_blend=get_value(context, node_tree, shader_node.inputs['DestBlendFunc'], int),
        pri_gradient=get_value(context, node_tree, shader_node.inputs['PriGradient'], int),
        sec_gradient=get_value(context, node_tree, shader_node.inputs['SecGradient'], int),
        src_blend=get_value(context, node_tree, shader_node.inputs['SrcBlendFunc'], int),
        detail_color_func=get_value(context, node_tree, shader_node.inputs['DetailColorFunc'], int),
        detail_alpha_func=get_value(context, node_tree, shader_node.inputs['DetailAlphaFunc'], int),
        shader_preset=get_value(context, node_tree, shader_node.inputs['Preset'], int),
        alpha_test=get_value(context, node_tree, shader_node.inputs['AlphaTest'], int),
        post_detail_color_func=get_value(context, node_tree, shader_node.inputs['PostDetailColorFunc'], int),
        post_detail_alpha_func=get_value(context, node_tree, shader_node.inputs['PostDetailAlphaFunc'], int))

    texture, uv_layer_name = get_texture_value(context, node_tree, shader_node.inputs['DiffuseTexture'])

    return vert_mat, shader, texture, uv_layer_name


def retrieve_shader_material(context, material, shader_node):
    node_tree = shader_node.node_tree
    name = node_tree.name
    shader_mat = ShaderMaterial(
        header=ShaderMaterialHeader(type_name=name))

    shader_mat.header.technique_index = get_value(context, node_tree, shader_node.inputs['Technique'], int)

    filename = name.replace('.fx', '.xml')

    for input in shader_node.inputs:
        if isinstance(input, NodeSocketTexture):
            prop_type = STRING_PROPERTY
            value = get_texture_value(context, node_tree, input)
        elif isinstance(input, NodeSocketTextureAlpha):
            continue
        elif isinstance(input, NodeSocketFloat):
            prop_type = FLOAT_PROPERTY
            value = get_value(context, node_tree, input, float)
        elif isinstance(input, NodeSocketVector2):
            prop_type = VEC2_PROPERTY
            value = get_vec2_value(context, node_tree, input)
        elif isinstance(input, NodeSocketVector):
            prop_type = VEC3_PROPERTY
            value = get_vec_value(context, node_tree, input)
        elif isinstance(input, (NodeSocketVector4, NodeSocketColor)):
            prop_type = VEC4_PROPERTY
            value = get_color_value(context, node_tree, input)
        elif isinstance(input, NodeSocketInt):
            prop_type = LONG_PROPERTY
            value = get_value(context, node_tree, input, int)
        elif isinstance(input, NodeSocketBool):
            prop_type = BOOL_PROPERTY
            value = get_value(context, node_tree, input, bool)
        else:
            context.warning('Invalid node socket type \'' + str(input) + '\'!')
            continue

        shader_mat.properties.append(ShaderMaterialProperty(type=prop_type, name=input.name, value=value))

    return shader_mat


def get_shader_node_group(context, node_tree):
    output_node = None

    for node in node_tree.nodes:
        if node.bl_idname == 'ShaderNodeOutputMaterial':
            output_node = node
            break

    if output_node is None:
        return None

    socket = output_node.inputs['Surface']
    if not socket.is_linked:
        return None

    for link in socket.links:
        if link.from_node.bl_idname == 'ShaderNodeGroup':
            return link.from_node
    # TODO: handle the default PrincipledBSDF here
    return None


def get_uv_layer_name(ontext, node_tree, socket):
    type = 'ShaderNodeUVMap'

    for link in socket.links:
        if link.from_node.bl_idname == type:
            return link.from_node.uv_map
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + socket.name + ' in ' + node_tree.name + ' is not of type ' + type)
    return None


def get_texture_value(context, node_tree, socket):
    type = 'ShaderNodeTexImage'

    for link in socket.links:
        if link.from_node.bl_idname == type:
            return link.from_node.image.name, get_uv_layer_name(context, node_tree, link.from_node.inputs['Vector'])
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + socket.name + ' in ' + node_tree.name + ' is not of type ' + type)
    return None, None


def get_value(context, node_tree, socket, cast):
    type = 'ShaderNodeValue'

    for link in socket.links:
        if link.from_node.bl_idname == type:
            return cast(link.from_node.outputs['Value'].default_value)
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + socket.name + ' in ' + node_tree.name + ' is not of type ' + type)
    return cast(socket.default_value)


def get_vec_value(context, node_tree, socket):
    for link in socket.links:
        return link.from_node.outputs['Vector'].default_value
    return socket.default_value


def get_vec2_value(context, node_tree, socket):
    return get_vec_value(context, node_tree, socket).xy


def get_color_value(context, node_tree, socket):
    type = 'ShaderNodeRGB'

    for link in socket.links:
        if link.from_node.bl_idname == type:
            return RGBA(vec=link.from_node.outputs['Color'].default_value)
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + socket.name + ' in ' + node_tree.name + ' is not of type ' + type)
    return RGBA(vec=socket.default_value)
