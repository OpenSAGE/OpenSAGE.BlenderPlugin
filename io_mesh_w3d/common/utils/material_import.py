# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *


#######################################################################################################################
# vertex material
#######################################################################################################################

def create_vertex_material(context, principleds, structure, mesh, name, triangles):
    for vertMat in structure.vert_materials:
        material, principled = create_material_from_vertex_material(name, vertMat)
        mesh.materials.append(material)
        principleds.append(principled)

    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    for mat_pass in structure.material_passes:
        get_or_create_uvlayer(context, mesh, b_mesh, triangles, mat_pass)

        if mat_pass.tx_stages:
            tx_stage = mat_pass.tx_stages[0]
            mat_id = mat_pass.vertex_material_ids[0]
            tex_id = tx_stage.tx_ids[0][0]
            texture = structure.textures[tex_id]
            tex = find_texture(context, texture.file, texture.id)
            principleds[mat_id].base_color_texture.image = tex


def create_material_from_vertex_material(name, vert_mat):
    name = name + "." + vert_mat.vm_name
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        return material, principled

    material = bpy.data.materials.new(name)
    material.material_type = 'VERTEX_MATERIAL'
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    attributes = {'DEFAULT'}
    attribs = vert_mat.vm_info.attributes
    if attribs & USE_DEPTH_CUE:
        attributes.add('USE_DEPTH_CUE')
    if attribs & ARGB_EMISSIVE_ONLY:
        attributes.add('ARGB_EMISSIVE_ONLY')
    if attribs & COPY_SPECULAR_TO_DIFFUSE:
        attributes.add('COPY_SPECULAR_TO_DIFFUSE')
    if attribs & DEPTH_CUE_TO_ALPHA:
        attributes.add('DEPTH_CUE_TO_ALPHA')

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    principled.base_color = vert_mat.vm_info.diffuse.to_vector_rgb()
    principled.alpha = vert_mat.vm_info.opacity
    principled.specular = vert_mat.vm_info.shininess

    material.attributes = attributes
    material.specular_color = vert_mat.vm_info.specular.to_vector_rgb()
    material.emission = vert_mat.vm_info.emissive.to_vector_rgba()
    material.ambient = vert_mat.vm_info.ambient.to_vector_rgba()
    material.translucency = vert_mat.vm_info.translucency

    material.vm_args_0 = vert_mat.vm_args_0
    material.vm_args_1 = vert_mat.vm_args_1

    return material, principled


#######################################################################################################################
# shader material
#######################################################################################################################

def create_shader_material(context, node_tree, shader_material):
    material_name = shader_material.type_name

    instance = node_tree.nodes.new(type='ShaderNodeGroup')
    instance.node_tree = bpy.data.node_groups[shader_material.type_name]
    instance.label = shader_material.type_name
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
            uv_node.uv_map = pipeline.uv_map
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
            y -= 300

        elif prop.type == VEC4_PROPERTY:
            instance.inputs[prop.name].default_value = prop.to_rgba()
        else:
            instance.inputs[prop.name].default_value = prop.value

    output = node_tree.nodes.get('Material Output')
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])



def create_material_from_shader_material(context, name, shader_mat):
    name = name + '.' + shader_mat.header.type_name
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        return material, principled

    material = bpy.data.materials.new(name)
    material.material_type = 'SHADER_MATERIAL'
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    material.technique = shader_mat.header.technique

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)

    for prop in shader_mat.properties:
        if prop.name == 'DiffuseTexture' and prop.value != '':
            principled.base_color_texture.image = find_texture(context, prop.value)
        elif prop.name == 'NormalMap' and prop.value != '':
            principled.normalmap_texture.image = find_texture(context, prop.value)
        elif prop.name == 'BumpScale':
            principled.normalmap_strength = prop.value
        elif prop.name == 'SpecMap' and prop.value != '':
            principled.specular_texture.image = find_texture(context, prop.value)
        elif prop.name == 'SpecularExponent' or prop.name == 'Shininess':
            material.specular_intensity = prop.value / 200.0
        elif prop.name == 'DiffuseColor' or prop.name == 'ColorDiffuse':
            material.diffuse_color = prop.to_rgba()
        elif prop.name == 'SpecularColor' or prop.name == 'ColorSpecular':
            material.specular_color = prop.to_rgb()
        elif prop.name == 'CullingEnable':
            material.use_backface_culling = prop.value
        elif prop.name == 'Texture_0':
            principled.base_color_texture.image = find_texture(context, prop.value)

        # all props below have no effect on shading -> custom properties for roundtrip purpose
        elif prop.name == 'AmbientColor' or prop.name == 'ColorAmbient':
            material.ambient = prop.to_rgba()
        elif prop.name == 'EmissiveColor' or prop.name == 'ColorEmissive':
            material.emission = prop.to_rgba()
        elif prop.name == 'Opacity':
            principled.alpha = prop.value
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
        elif prop.name == 'Texture_1':  # second diffuse texture
            material.texture_1 = prop.value
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

    return material, principled


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


