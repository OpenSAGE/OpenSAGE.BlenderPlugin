# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3d.structs.mesh_structs.shader import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *


def append_texture_if_valid(texture, used_textures):
    if isinstance(texture, str):
        if texture != '' and texture not in used_textures:
            used_textures.append(texture)
    elif texture is not None and texture.image is not None and texture.image.name not in used_textures:
        used_textures.append(texture.image.name)
    return used_textures


def get_used_textures(material, principled, used_textures):
    used_textures = append_texture_if_valid(principled.base_color_texture, used_textures)
    used_textures = append_texture_if_valid(principled.normalmap_texture, used_textures)
    used_textures = append_texture_if_valid(principled.specular_texture, used_textures)

    used_textures = append_texture_if_valid(material.texture_1, used_textures)
    used_textures = append_texture_if_valid(material.environment_texture, used_textures)
    used_textures = append_texture_if_valid(material.recolor_texture, used_textures)
    used_textures = append_texture_if_valid(material.scrolling_mask_texture, used_textures)
    return used_textures


def retrieve_vertex_material(material, principled):
    info = VertexMaterialInfo(
        attributes=0,
        shininess=principled.specular,
        specular=RGBA(vec=material.specular_color, a=0),
        diffuse=RGBA(vec=material.diffuse_color, a=0),
        emissive=RGBA(vec=material.emission),
        ambient=RGBA(vec=material.ambient),
        translucency=material.translucency,
        opacity=principled.alpha)

    if 'USE_DEPTH_CUE' in material.attributes:
        info.attributes |= USE_DEPTH_CUE
    if 'ARGB_EMISSIVE_ONLY' in material.attributes:
        info.attributes |= ARGB_EMISSIVE_ONLY
    if 'COPY_SPECULAR_TO_DIFFUSE' in material.attributes:
        info.attributes |= COPY_SPECULAR_TO_DIFFUSE
    if 'DEPTH_CUE_TO_ALPHA' in material.attributes:
        info.attributes |= DEPTH_CUE_TO_ALPHA

    vert_material = VertexMaterial(
        vm_name=material.name.split('.', 1)[-1],
        vm_info=info,
        vm_args_0=material.vm_args_0,
        vm_args_1=material.vm_args_1)

    return vert_material


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
    elif type == 5 and default is None:
        default = Vector()
    elif type == 6 and default is None:
        default = 0
    elif type == 7 and default is None:
        default = False

    if value == default:
        return
    shader_mat.properties.append(ShaderMaterialProperty(type=type, name=name, value=value))


def to_vec(color):
    return Vector((color[0], color[1], color[2], color[3] if len(color) > 3 else 1.0))


def retrieve_shader_material(context, material, principled, w3x=False):
    name = material.name.split('.', 1)[-1]
    if not name.endswith('.fx'):
        context.info('\'' + name + '\' is not a valid shader name -> defaulting to: \'DefaultW3D.fx\'')
        name = 'DefaultW3D.fx'

    shader_mat = ShaderMaterial(header=ShaderMaterialHeader(type_name=name), properties=[])

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
        append_property(shader_mat, 5, 'TexCoordTransform_0', to_vec(material.tex_coord_transform_0))
        append_property(shader_mat, 5, 'TexCoordTransform_1', to_vec(material.tex_coord_transform_1))
    else:
        append_property(shader_mat, 1, 'DiffuseTexture', principled.base_color_texture)

    append_property(shader_mat, 1, 'NormalMap', principled.normalmap_texture)
    if principled.normalmap_texture is not None and principled.normalmap_texture.image is not None:
        if shader_mat.header.type_name == 'DefaultW3D.fx':
            shader_mat.header.type_name = 'NormalMapped.fx'
        append_property(shader_mat, 2, 'BumpScale', principled.normalmap_strength, 1.0)

    append_property(shader_mat, 1, 'SpecMap', principled.specular_texture)
    append_property(shader_mat, 7, 'CullingEnable', material.use_backface_culling)
    append_property(shader_mat, 2, 'Opacity', principled.alpha, 1.0)
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
        depth_compare=int(material.shader.depth_compare),
        depth_mask=int(material.shader.depth_mask),
        color_mask=material.shader.color_mask,
        dest_blend=int(material.shader.dest_blend),
        fog_func=material.shader.fog_func,
        pri_gradient=int(material.shader.pri_gradient),
        sec_gradient=int(material.shader.sec_gradient),
        src_blend=int(material.shader.src_blend),
        texturing=0,  # is set to 1 if textures are applied
        detail_color_func=int(material.shader.detail_color_func),
        detail_alpha_func=int(material.shader.detail_alpha_func),
        shader_preset=material.shader.shader_preset,
        alpha_test=int(material.shader.alpha_test),
        post_detail_color_func=int(material.shader.post_detail_color_func),
        post_detail_alpha_func=int(material.shader.post_detail_alpha_func))
