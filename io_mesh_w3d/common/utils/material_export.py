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

    #if shader_node.node_tree.name == VertexMaterialGroup.name:
    #elif shader_node.node_tree.name == PrelitUnlitGroup.name:
    #elif shader_node.node_tree.name == PrelitVertexGroup.name:
    #elif shader_node.node_tree.name == PrelitLightmapMultiPassGroup.name:
    #elif shader_node.node_tree.name == PrelitLightmapMultiTextureGroup.name:

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
        texturing=get_value(context, node_tree, shader_node, 'Texturing', int), #TODO: set this based on applied texture
        detail_color_func=get_value(context, node_tree, shader_node, 'DetailColorFunc', int),
        detail_alpha_func=get_value(context, node_tree, shader_node, 'DetailAlphaFunc', int),
        shader_preset=get_value(context, node_tree, shader_node, 'Preset', int),
        alpha_test=get_value(context, node_tree, shader_node, 'AlphaTest', int),
        post_detail_color_func=get_value(context, node_tree, shader_node, 'PostDetailColorFunc', int),
        post_detail_alpha_func=get_value(context, node_tree, shader_node, 'PostDetailAlphaFunc', int))

    (texture, uv_map) = get_texture_value(context, node_tree, shader_node, 'DiffuseTexture')

    texture_struct = Texture(file=texture)
    tx_coords = 


    #return vert_mat, shader, texture_struct, tx_coords, pass_index, prelit_type
    return vert_mat


def append_property(shader_mat, type, name, value, default=None):
    if value is None:
        return
    if type == 1:
        if isinstance(value, str):
            if value == '':  # default
                return
        elif value.image is None:
            return
        else:
            value = value.image.name
    elif type == 2:
        if default is None:
            default = 0.0
        if abs(value - default) < 0.01:
            return
    elif type == 3 and default is None:
        default = Vector().xy
    elif type == 4 and default is None:
        default = Vector()
    elif type == 5 and default is None:
        default = Vector((0.0, 0.0, 0.0, 1.0))
    elif type == 6 and default is None:
        default = 0
    elif type == 7 and default is None:
        default = False

    if value == default:
        return
    shader_mat.properties.append(ShaderMaterialProperty(
        type=type, name=name, value=value))


def to_vec(color):
    return Vector((color[0], color[1], color[2], color[3] if len(color) > 3 else 1.0))


def retrieve_shader_material(context, material, principled, w3x=False):
    name = material.name.split('.', 1)[-1]
    if not name.endswith('.fx'):
        context.info(name + ' is not a valid shader name -> defaulting to: DefaultW3D.fx')
        name = 'DefaultW3D.fx'

    shader_mat = ShaderMaterial(
        header=ShaderMaterialHeader(
            type_name=name),
        properties=[])

    shader_mat.header.technique_index = material.technique

    if w3x:
        append_property(shader_mat, 2, 'Shininess', material.specular_intensity * 200.0, 100.0)
        append_property(shader_mat, 5, 'ColorDiffuse', to_vec(material.diffuse_color), Vector((0.8, 0.8, 0.8, 1.0)))
        append_property(shader_mat, 5, 'ColorSpecular', to_vec(material.specular_color), Vector((1.0, 1.0, 1.0, 1.0)))
        append_property(shader_mat, 5, 'ColorAmbient', to_vec(material.ambient), Vector((1.0, 1.0, 1.0, 0.0)))
        append_property(shader_mat, 5, 'ColorEmissive', to_vec(material.emission), Vector((1.0, 1.0, 1.0, 0.0)))

    else:
        append_property(shader_mat, 2, 'SpecularExponent', material.specular_intensity * 200.0, 100.0)
        append_property(shader_mat, 5, 'DiffuseColor', to_vec(material.diffuse_color), Vector((0.8, 0.8, 0.8, 1.0)))
        append_property(shader_mat, 5, 'SpecularColor', to_vec(material.specular_color), Vector((1.0, 1.0, 1.0, 1.0)))
        append_property(shader_mat, 5, 'AmbientColor', to_vec(material.ambient), Vector((1.0, 1.0, 1.0, 0.0)))
        append_property(shader_mat, 5, 'EmissiveColor', to_vec(material.emission), Vector((1.0, 1.0, 1.0, 0.0)))

    if material.texture_1:
        append_property(shader_mat, 1, 'Texture_0', principled.base_color_texture)
        append_property(shader_mat, 1, 'Texture_1', material.texture_1)
        append_property(shader_mat, 6, 'NumTextures', 2)
        append_property(shader_mat, 6, 'SecondaryTextureBlendMode', material.secondary_texture_blend_mode)
        append_property(shader_mat, 6, 'TexCoordMapper_0', material.tex_coord_mapper_0)
        append_property(shader_mat, 6, 'TexCoordMapper_1', material.tex_coord_mapper_1)
        append_property(shader_mat, 5, 'TexCoordTransform_0', to_vec(material.tex_coord_transform_0), Vector())
        append_property(shader_mat, 5, 'TexCoordTransform_1', to_vec(material.tex_coord_transform_1), Vector())
    else:
        append_property(shader_mat, 1, 'DiffuseTexture', principled.base_color_texture)

    append_property(shader_mat, 1, 'NormalMap', principled.normalmap_texture)
    if principled.normalmap_texture is not None and principled.normalmap_texture.image is not None:
        if shader_mat.header.type_name == 'DefaultW3D.fx':
            shader_mat.header.type_name = 'NormalMapped.fx'
        append_property(shader_mat, 2, 'BumpScale', principled.normalmap_strength, 1.0)

    append_property(shader_mat, 1, 'SpecMap', principled.specular_texture)
    append_property(shader_mat, 7, 'CullingEnable', material.use_backface_culling)
    append_property(shader_mat, 2, 'Opacity', material.opacity)
    append_property(shader_mat, 7, 'AlphaTestEnable', material.alpha_test, True)
    append_property(shader_mat, 6, 'BlendMode', material.blend_mode)
    append_property(shader_mat, 3, 'BumpUVScale', material.bump_uv_scale)
    append_property(shader_mat, 6, 'EdgeFadeOut', material.edge_fade_out)
    append_property(shader_mat, 7, 'DepthWriteEnable', material.depth_write)
    append_property(shader_mat, 5, 'Sampler_ClampU_ClampV_NoMip_0',
                    material.sampler_clamp_uv_no_mip_0, Vector((0.0, 0.0, 0.0, 0.0)))
    append_property(shader_mat, 5, 'Sampler_ClampU_ClampV_NoMip_1',
                    material.sampler_clamp_uv_no_mip_1, Vector((0.0, 0.0, 0.0, 0.0)))
    append_property(shader_mat, 1, 'EnvironmentTexture', material.environment_texture)
    append_property(shader_mat, 2, 'EnvMult', material.environment_mult)
    append_property(shader_mat, 1, 'RecolorTexture', material.recolor_texture)
    append_property(shader_mat, 2, 'RecolorMultiplier', material.recolor_mult)
    append_property(shader_mat, 7, 'UseRecolorColors', material.use_recolor)
    append_property(shader_mat, 7, 'HouseColorPulse', material.house_color_pulse)
    append_property(shader_mat, 1, 'ScrollingMaskTexture', material.scrolling_mask_texture)
    append_property(shader_mat, 2, 'TexCoordTransformAngle_0', material.tex_coord_transform_angle)
    append_property(shader_mat, 2, 'TexCoordTransformU_0', material.tex_coord_transform_u_0)
    append_property(shader_mat, 2, 'TexCoordTransformV_0', material.tex_coord_transform_v_0)
    append_property(shader_mat, 2, 'TexCoordTransformU_1', material.tex_coord_transform_u_1)
    append_property(shader_mat, 2, 'TexCoordTransformV_1', material.tex_coord_transform_v_1)
    append_property(shader_mat, 2, 'TexCoordTransformU_2', material.tex_coord_transform_u_2)
    append_property(shader_mat, 2, 'TexCoordTransformV_2', material.tex_coord_transform_v_2)
    append_property(shader_mat, 5, 'TextureAnimation_FPS_NumPerRow_LastFrame_FrameOffset_0',
                    material.tex_ani_fps_NPR_lastFrame_frameOffset_0, Vector((0.0, 0.0, 0.0, 0.0)))
    append_property(shader_mat, 1, 'IonHullTexture', material.ion_hull_texture)
    append_property(shader_mat, 7, 'MultiTextureEnable', material.multi_texture_enable)

    return shader_mat


def retrieve_shader(material):
    return Shader(
        depth_compare=material.shader.depth_compare,
        depth_mask=material.shader.depth_mask,
        color_mask=material.shader.color_mask,
        dest_blend=material.shader.dest_blend,
        fog_func=material.shader.fog_func,
        pri_gradient=material.shader.pri_gradient,
        sec_gradient=material.shader.sec_gradient,
        src_blend=material.shader.src_blend,
        texturing=material.shader.texturing,
        detail_color_func=material.shader.detail_color_func,
        detail_alpha_func=material.shader.detail_alpha_func,
        shader_preset=material.shader.shader_preset,
        alpha_test=material.shader.alpha_test,
        post_detail_color_func=material.shader.post_detail_color_func,
        post_detail_alpha_func=material.shader.post_detail_alpha_func)
