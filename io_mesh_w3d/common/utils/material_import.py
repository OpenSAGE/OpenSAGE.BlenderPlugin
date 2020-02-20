# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *

    #node.color = (1, 0, 0)
    #node.use_custom_color = True
    #node.name = 'Test'
    #node.label

def register_w3d_material_node_group():
    group = bpy.data.node_groups.new('W3DMaterial', 'ShaderNodeTree')
    node_tree = group
    links = node_tree.links

    # create group inputs
    group_inputs = group.nodes.new('NodeGroupInput')
    group_inputs.location = (-350,0)
    group.inputs.new('NodeSocketColor', 'Diffuse')
    group.inputs.new('NodeSocketFloat', 'Alpha')
    group.inputs['Alpha'].default_value = 1.0
    group.inputs.new('NodeSocketColor', 'Diffuse2')
    group.inputs.new('NodeSocketFloat', 'Alpha2')
    group.inputs.new('NodeSocketInt', 'DestBlend')
    group.inputs['DestBlend'].default_value = 0
    group.inputs['DestBlend'].min_value = 0
    group.inputs['DestBlend'].max_value = 1
    group.inputs.new('NodeSocketColor', 'Specular')
    group.inputs.new('NodeSocketFloat', 'Roughness')
    group.inputs.new('NodeSocketColor', 'Emissive')
    group.inputs.new('NodeSocketColor', 'Normal')
    group.inputs.new('NodeSocketFloat', 'Strength')
    

    # create group outputs
    group_outputs = group.nodes.new('NodeGroupOutput')
    group_outputs.location = (300,0)
    group.outputs.new('NodeSocketShader', 'BSDF')

    # create and link nodes
    mix = create_rgb_mix_node(node_tree)
    mix.location = (-100, 200)
    links.new(group_inputs.outputs['Diffuse'], mix.inputs['Color1'])
    links.new(group_inputs.outputs['Diffuse2'], mix.inputs['Color2'])
    links.new(group_inputs.outputs['Alpha2'], mix.inputs['Fac'])

    alpha_pipeline = node_tree.nodes.new(type='ShaderNodeGroup')
    alpha_pipeline.location = (-100, 0)
    alpha_pipeline.node_tree = bpy.data.node_groups['W3DAlphaPipeline']
    links.new(group_inputs.outputs['Diffuse'], alpha_pipeline.inputs['Diffuse'])
    links.new(group_inputs.outputs['Alpha'], alpha_pipeline.inputs['Alpha'])
    links.new(group_inputs.outputs['DestBlend'], alpha_pipeline.inputs['DestBlend'])

    normal = create_normal_map_node(node_tree)
    normal.location = (-100, -200)
    links.new(group_inputs.outputs['Normal'], normal.inputs['Color'])
    links.new(group_inputs.outputs['Strength'], normal.inputs['Strength'])

    shader = create_specular_shader_node(node_tree)
    shader.location = (100, 0)
    links.new(mix.outputs['Color'], shader.inputs['Base Color'])
    links.new(group_inputs.outputs['Specular'], shader.inputs['Specular'])
    links.new(group_inputs.outputs['Roughness'], shader.inputs['Roughness'])
    links.new(group_inputs.outputs['Emissive'], shader.inputs['Emissive Color'])
    links.new(alpha_pipeline.outputs['Alpha'], shader.inputs['Transparency'])
    links.new(normal.outputs['Normal'], shader.inputs['Normal'])
    links.new(shader.outputs['BSDF'], group_outputs.inputs['BSDF'])


def register_alpha_node_group():
    group = bpy.data.node_groups.new('W3DAlphaPipeline', 'ShaderNodeTree')
    node_tree = group
    links = node_tree.links

    # create group inputs
    group_inputs = group.nodes.new('NodeGroupInput')
    group_inputs.location = (-500,0)
    group.inputs.new('NodeSocketColor', 'Diffuse')
    group.inputs.new('NodeSocketFloat', 'Alpha')
    group.inputs['Alpha'].default_value = 1.0
    group.inputs.new('NodeSocketInt', 'DestBlend')
    group.inputs['DestBlend'].default_value = 0
    group.inputs['DestBlend'].min_value = 0
    group.inputs['DestBlend'].max_value = 1

    # create group outputs
    group_outputs = group.nodes.new('NodeGroupOutput')
    group_outputs.location = (500,0)
    group.outputs.new('NodeSocketFloat', 'Alpha')

    # default texture alpha
    compare_1 = create_math_node(node_tree, mode='COMPARE')
    compare_1.location = (-200, 100)
    compare_1.inputs[0].default_value = 0
    links.new(group_inputs.outputs['DestBlend'], compare_1.inputs[1])
    links.new(group_inputs.outputs['Alpha'], compare_1.inputs[2])

    # v of diffuse
    seperate_hsv = create_seperate_hsv_node(node_tree)
    seperate_hsv.location = (-300, -100)
    links.new(group_inputs.outputs['Diffuse'], seperate_hsv.inputs['Color'])

    compare_2 = create_math_node(node_tree, mode='COMPARE')
    compare_2.location = (-100, -100)
    compare_2.inputs[0].default_value = 1
    links.new(group_inputs.outputs['DestBlend'], compare_2.inputs[1])
    links.new(seperate_hsv.outputs['V'], compare_2.inputs[2])

    # both
    add_node = create_math_node(node_tree, mode='ADD')
    add_node.location = (100, 0)
    links.new(compare_1.outputs['Value'], add_node.inputs[0])
    links.new(compare_2.outputs['Value'], add_node.inputs[1])

    subtract_node = create_math_node(node_tree, mode='SUBTRACT')
    subtract_node.location = (300, 0)
    subtract_node.inputs[0].default_value = 1.0
    links.new(add_node.outputs['Value'], subtract_node.inputs[1])
    links.new(subtract_node.outputs['Value'], group_outputs.inputs['Alpha'])


def get_connected_nodes(links, node, input, types=[]):
    nodes = []
    for link in links:
        #print(link.to_node)
        #print(link.to_socket)
        if link.to_node == node and link.to_socket.identifier == input:
            # and link.from_socket in outputs:
            # and type(node) == bpy.types.ShaderNodeTexture....
            # and node.inputs[''].is_linked
            nodes.append(link.from_node)

    for node in nodes:
        print('###')
        print(node.bl_idname)
        print(node.name)
    return nodes


def create_specular_shader_node(node_tree):
    # inputs: Base Color, Specular, Roughness, Emissive Color, Transparency,
    #           Normal, Clear Coat, Clear Coat Radius, Clear Coat Normal, Ambient Occlusion
    # outputs: BSDF

    node = node_tree.nodes.new('ShaderNodeEeveeSpecular')
    node.label = 'Shader'
    # hide unused inputs
    node.inputs['Clear Coat'].hide = True
    node.inputs['Clear Coat Roughness'].hide = True
    node.inputs['Clear Coat Normal'].hide = True
    node.inputs['Ambient Occlusion'].hide = True
    return node


def create_texture_node(node_tree, texture):
    # inputs: Vector
    # outputs: Color, Alpha

    node = node_tree.nodes.new('ShaderNodeTexImage')
    #node.color_mapping
    #node.extension # interpolation past bounds
    node.image = texture
    #node.image_user
    #node.interpolation
    #node.projection
    #node.projection_blend
    #node.texture_mapping
    return node

def create_uv_map_node(node_tree):
    # outputs: UV

    node = node_tree.nodes.new('ShaderNodeUVMap')
    #node.uv_map = 'uvmapname'
    return node

def create_math_node(node_tree, mode='SUBTRACT'):
    # inputs: Value, Value
    # outputs: Value

    node = node_tree.nodes.new('ShaderNodeMath')
    node.operation = mode
    #node.clamp = False
    return node

def create_rgb_mix_node(node_tree):
    # inputs: Fac, Color1, Color2
    # outputs: Color

    node = node_tree.nodes.new('ShaderNodeMixRGB')
    #node.blend_type
    #node.use_alpha
    #node.use_clamp
    return node

def create_normal_map_node(node_tree):
    # inputs: Strength, Color
    # outputs: Normal

    node = node_tree.nodes.new('ShaderNodeNormalMap')
    node.space = 'TANGENT'
    #node.uv_map = 'uvmapname'
    return node

def create_seperate_hsv_node(node_tree):
    # inputs: Color
    # outputs: H, S, V

    node = node_tree.nodes.new('ShaderNodeSeparateHSV')
    return node

def create_rgb_node(node_tree):
    # outputs: Color

    node = node_tree.nodes.new('ShaderNodeRGB')
    return node




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



def create_material_passes(context, base_struct, mesh, triangles):
    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    for i, mat_pass in enumerate(base_struct.material_passes):
        vert_materials = []
        shaders = []
        textures = []
        shader_materials = []
        tx_coords = []

        #TODO: create vert_mat - shader - texture combinations
        for vert_mat_id in mat_pass.vertex_material_ids:
            vert_materials.append(base_struct.vert_materials[vert_mat_id])

        for shader_id in mat_pass.shader_ids:
            shaders.append(base_struct.shaders[shader_id])

        for tx_stage in mat_pass.tx_stages:
            textures.append(base_struct.textures[tx_stage.tx_ids[0]])
            tx_coords.append(tx_stage.tx_coords)

        for shader_mat_id in mat_pass.shader_material_ids:
            shader_materials.append(base_struct.shader_materials[shader_mat_id])

        if mat_pass.tx_coords:
            tx_coords.append(mat_pass.tx_coords)

        print('vert: ' + str(len(vert_materials)))
        print('shaders: ' + str(len(shaders)))
        print('textures: ' + str(len(textures)))
        print('shader_materials: ' + str(len(shader_materials)))
        print('tx_coords: ' + str(len(tx_coords)))

        if vert_materials:
            texture = None
            if textures:
                texture = textures[0]
            tx_coordinates = None
            if tx_coords:
                tx_coordinates = tx_coords[0]
            create_vertex_material(context, mesh, b_mesh, triangles, vert_materials[0], shaders[0], texture, tx_coordinates)

        if shader_materials:
            create_shader_material(context, mesh, b_mesh, triangles, shader_materials[0], tx_coords[0])



##########################################################################
# vertex material
##########################################################################

def create_vertex_material(context, mesh, b_mesh, triangles, vert_mat, shader, texture_struct, tx_coords):
    material = bpy.data.materials.new(mesh.name)
    mesh.materials.append(material)

    material.material_type = 'VERTEX_MATERIAL'
    material.prelit_type = 'PRELIT_UNLIT'
    material.use_nodes = True
    material.shadow_method = 'CLIP'
    material.blend_method = 'BLEND'
    material.show_transparent_back = False
    #material.pass_index = index

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

    # TODO: map these to shader node properties
    material.ambient = vert_mat.vm_info.ambient.to_vector_rgba()
    material.translucency = vert_mat.vm_info.translucency
    material.opacity = vert_mat.vm_info.opacity

    material.vm_args_0 = vert_mat.vm_args_0
    material.vm_args_1 = vert_mat.vm_args_1

    set_shader_properties(material, shader)

    # get or create node group
    node_tree = material.node_tree
    links = node_tree.links

    # delete principled bsdf
    principled_bsdf = node_tree.nodes.get('Principled BSDF')
    node_tree.nodes.remove(principled_bsdf)
    
    inst = node_tree.nodes.new(type='ShaderNodeGroup')
    inst.location = (0, 300)
    inst.node_tree = bpy.data.node_groups['W3DMaterial']
    inst.label = vert_mat.vm_name

    inst.inputs['Specular'].default_value = vert_mat.vm_info.specular.to_vector_rgba()
    inst.inputs['Roughness'].default_value = vert_mat.vm_info.shininess
    inst.inputs['Emissive'].default_value = vert_mat.vm_info.emissive.to_vector_rgba()

    output = node_tree.nodes.get('Material Output')
    links.new(inst.outputs['BSDF'], output.inputs['Surface'])

    if texture_struct is not None:
        texture = find_texture(context, texture_struct.file, texture_struct.id)

        texture_node = create_texture_node(node_tree, texture)
        texture_node.location = (-250, 0)
        links.new(texture_node.outputs['Color'], inst.inputs['Diffuse'])
        links.new(texture_node.outputs['Alpha'], inst.inputs['Alpha'])

        uv_layer = get_or_create_uv_layer(mesh, b_mesh, triangles, tx_coords)

        uv_node = create_uv_map_node(node_tree)
        uv_node.uv_map = uv_layer
        uv_node.location = (-450, 0)
        links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])


##########################################################################
# shader material
##########################################################################


def create_shader_material(context, mesh, b_mesh, triangles, shader_mat, tx_coords):
    material = bpy.data.materials.new(mesh.name)
    mesh.materials.append(material)
    material.material_type = 'SHADER_MATERIAL'
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    if shader_mat.header.technique is not None:
        material.technique = shader_mat.header.technique

    # get or create node group
    node_tree = material.node_tree
    links = node_tree.links

    # delete principled bsdf
    principled_bsdf = node_tree.nodes.get('Principled BSDF')
    node_tree.nodes.remove(principled_bsdf)

    inst = node_tree.nodes.new(type='ShaderNodeGroup')
    inst.location = (0, 300)
    inst.node_tree = bpy.data.node_groups['W3DMaterial']
    inst.label = shader_mat.header.type_name

    output = node_tree.nodes.get('Material Output')
    links.new(inst.outputs['BSDF'], output.inputs['Surface'])

    uv_layer = get_or_create_uv_layer(mesh, b_mesh, triangles, tx_coords)

    for prop in shader_mat.properties:
        if prop.name in ['DiffuseTexture', 'Texture_0'] and prop.value != '':
            texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
            texture_node.location = (-550, 600)
            links.new(texture_node.outputs['Color'], inst.inputs['Diffuse'])
            links.new(texture_node.outputs['Alpha'], inst.inputs['Alpha'])

            uv_node = create_uv_map_node(node_tree)
            uv_node.uv_map = uv_layer
            uv_node.location = (-750, 600)
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
        elif prop.name == 'NormalMap' and prop.value != '':
            texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
            texture_node.location = (-550, -300)
            links.new(texture_node.outputs['Color'], inst.inputs['Normal'])

            uv_node = create_uv_map_node(node_tree)
            uv_node.uv_map = uv_layer
            uv_node.location = (-750, -300)
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
        elif prop.name == 'BumpScale':
            inst.inputs['Strength'].default_value = prop.value
        elif prop.name == 'SpecMap' and prop.value != '':
            texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
            texture_node.location = (-550, 0)
            links.new(texture_node.outputs['Color'], inst.inputs['Specular'])

            uv_node = create_uv_map_node(node_tree)
            uv_node.uv_map = uv_layer
            uv_node.location = (-750, 0)
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
        elif prop.name == 'SpecularExponent' or prop.name == 'Shininess':
            inst.inputs['Roughness'].default_value = prop.value / 200.0
        elif prop.name == 'DiffuseColor' or prop.name == 'ColorDiffuse':
            material.diffuse_color = prop.to_rgba()
        elif prop.name == 'SpecularColor' or prop.name == 'ColorSpecular':
            material.specular_color = prop.to_rgb()
        elif prop.name == 'CullingEnable':
            material.use_backface_culling = prop.value
        elif prop.name == 'Texture_1':
            texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
            texture_node.location = (-550, 300)
            links.new(texture_node.outputs['Color'], inst.inputs['Diffuse2'])
            links.new(texture_node.outputs['Alpha'], inst.inputs['Alpha2'])

            uv_node = create_uv_map_node(node_tree)
            uv_node.uv_map = uv_layer
            uv_node.location = (-750, 300)
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])

        # all props below have no effect on shading -> custom properties for roundtrip purpose
        elif prop.name == 'AmbientColor' or prop.name == 'ColorAmbient':
            material.ambient = prop.to_rgba()
        elif prop.name == 'EmissiveColor' or prop.name == 'ColorEmissive':
            material.emission = prop.to_rgba()
        elif prop.name == 'Opacity':
            material.opacity = prop.value
        elif prop.name == 'AlphaTestEnable':
            material.alpha_test = prop.value
        elif prop.name == 'BlendMode':  # is blend_method ?
            material.blend_mode = prop.value
        elif prop.name == 'BumpUVScale':
            material.bump_uv_scale = prop.value.xy
        elif prop.name == 'EdgeFadeOut':
            material.edge_fade_out = prop.value
        elif prop.name == 'DepthWriteEnable':
            material.depth_write = prop.value
        elif prop.name == 'Sampler_ClampU_ClampV_NoMip_0':
            material.sampler_clamp_uv_no_mip_0 = prop.value
        elif prop.name == 'Sampler_ClampU_ClampV_NoMip_1':
            material.sampler_clamp_uv_no_mip_1 = prop.value
        elif prop.name == 'NumTextures':
            material.num_textures = prop.value  # is 1 if texture_0 and texture_1 are set
        elif prop.name == 'SecondaryTextureBlendMode':
            material.secondary_texture_blend_mode = prop.value
        elif prop.name == 'TexCoordMapper_0':
            material.tex_coord_mapper_0 = prop.value
        elif prop.name == 'TexCoordMapper_1':
            material.tex_coord_mapper_1 = prop.value
        elif prop.name == 'TexCoordTransform_0':
            material.tex_coord_transform_0 = prop.value
        elif prop.name == 'TexCoordTransform_1':
            material.tex_coord_transform_1 = prop.value
        elif prop.name == 'EnvironmentTexture':
            material.environment_texture = prop.value
        elif prop.name == 'EnvMult':
            material.environment_mult = prop.value
        elif prop.name == 'RecolorTexture':
            material.recolor_texture = prop.value
        elif prop.name == 'RecolorMultiplier':
            material.recolor_mult = prop.value
        elif prop.name == 'UseRecolorColors':
            material.use_recolor = prop.value
        elif prop.name == 'HouseColorPulse':
            material.house_color_pulse = prop.value
        elif prop.name == 'ScrollingMaskTexture':
            material.scrolling_mask_texture = prop.value
        elif prop.name == 'TexCoordTransformAngle_0':
            material.tex_coord_transform_angle = prop.value
        elif prop.name == 'TexCoordTransformU_0':
            material.tex_coord_transform_u_0 = prop.value
        elif prop.name == 'TexCoordTransformV_0':
            material.tex_coord_transform_v_0 = prop.value
        elif prop.name == 'TexCoordTransformU_1':
            material.tex_coord_transform_u_1 = prop.value
        elif prop.name == 'TexCoordTransformV_1':
            material.tex_coord_transform_v_1 = prop.value
        elif prop.name == 'TexCoordTransformU_2':
            material.tex_coord_transform_u_2 = prop.value
        elif prop.name == 'TexCoordTransformV_2':
            material.tex_coord_transform_v_2 = prop.value
        elif prop.name == 'TextureAnimation_FPS_NumPerRow_LastFrame_FrameOffset_0':
            material.tex_ani_fps_NPR_lastFrame_frameOffset_0 = prop.value
        elif prop.name == 'IonHullTexture':
            material.ion_hull_texture = prop.value
        elif prop.name == 'MultiTextureEnable':
            material.multi_texture_enable = prop.value
        else:
            context.error('shader property not implemented: ' + prop.name)


##########################################################################
# set shader properties
##########################################################################


def set_shader_properties(material, shader):
    material.shader.depth_compare = shader.depth_compare
    material.shader.depth_mask = shader.depth_mask
    material.shader.color_mask = shader.color_mask
    material.shader.dest_blend = shader.dest_blend
    material.shader.fog_func = shader.fog_func
    material.shader.pri_gradient = shader.pri_gradient
    material.shader.sec_gradient = shader.sec_gradient
    material.shader.src_blend = shader.src_blend
    material.shader.texturing = shader.texturing
    material.shader.detail_color_func = shader.detail_color_func
    material.shader.detail_alpha_func = shader.detail_alpha_func
    material.shader.shader_preset = shader.shader_preset
    material.shader.alpha_test = shader.alpha_test
    material.shader.post_detail_color_func = shader.post_detail_color_func
    material.shader.post_detail_alpha_func = shader.post_detail_alpha_func