import bpy
from bpy.props import *
from bpy.types import Material, PropertyGroup

# property definition
# input name : custom property name

material_parameter_map = {
("BuildingsSoviet", "BuildingsAllied", "BuildingsJapan"): {
    "__Preview": "preview_holes_trigger",
    "__FactionColor": "faction_color",

    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "SpecMap":"spec_texture",
    "DamagedTexture":"damaged_texture",
    "EnvMult":"environment_mult",
},

("BuildingsGeneric",): {
    "__Preview": "preview_holes_trigger",

    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "SpecMap":"spec_texture",
    "DamagedTexture":"damaged_texture",
    "EnvMult":"environment_mult",
},

("NormalMapped",): {
    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "DamagedTexture":"damaged_texture",
    "BumpScale":"bump_uv_scale",
    "AmbientColor":"ambient_color3",
    "DiffuseColor":"diffuse_color4",
    "SpecularColor":"specular_color_alt",
    "SpecularExponent":"specular_intensity_alt",
    "EnvMult":"environment_mult",
    "AlphaTestEnable":"alpha_test",    
},


("BuildingsGenericDamageFill",) : {
    "__Preview": "preview_holes_trigger",

    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "SpecMap":"spec_texture",
    "DamagedTexture":"damaged_texture",
    "BumpScale":"bump_uv_scale",
    "AmbientColor":"ambient_color3",
    "DiffuseColor":"diffuse_color4",
    "SpecularColor":"specular_color_alt",
    "SpecularExponent":"specular_intensity_alt",
    "EnvMult":"environment_mult"
},

("ObjectsSoviet", "ObjectsAllied", "ObjectsJapan"):{
    "__FactionColor": "faction_color",

    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "SpecMap":"spec_texture",
    "EnvMult":"environment_mult",
    "AlphaTestEnable":"alpha_test",
},

("ObjectsTerrain",):{
    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "SpecMap":"spec_texture",
    "EnvMult":"environment_mult",
    "AlphaTestEnable":"alpha_test",
},

("ObjectsAlliedTread",):{
    "__Preview": "preview_scrolling_trigger",

    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "SpecMap":"spec_texture",
    "EnvMult":"environment_mult",
    "AlphaTestEnable":"alpha_test",
},

("ObjectsGeneric",):{
    "DiffuseTexture":"diffuse_texture",
    "NormalMap":"normal_texture",
    "SpecMap":"spec_texture",
    "EnvMult":"environment_mult",
    "BumpScale":"bump_uv_scale",
    "AmbientColor":"ambient_color3",
    "DiffuseColor":"diffuse_color4",
    "SpecularColor":"specular_color_alt",
    "SpecularExponent":"specular_intensity_alt",
    "EnvMult":"environment_mult",
    "AlphaTestEnable":"alpha_test",
},

("Infantry",):{
    "__FactionColor": "faction_color",

    "ColorAmbient":"ambient_color3",
    "ColorDiffuse":"diffuse_color3",
    "ColorSpecular":"specular_color_alt",
    "Shininess":"specular_intensity_alt",
    "ColorEmissive":"emission_color",
    "Texture_0":"texture_0",
    "DepthWriteEnable":"depth_write",
    "AlphaTestEnable":"alpha_test",
    "CullingEnable":"use_backface_culling",
    "BlendMode":"blend_mode",    
},


("Tree", "BasicW3D"):{
    "ColorAmbient":"ambient_color3",
    "ColorDiffuse":"diffuse_color3",
    "ColorSpecular":"specular_color_alt",
    "Shininess":"specular_intensity_alt",
    "ColorEmissive":"emission_color",
    "Texture_0":"texture_0",
    "DepthWriteEnable":"depth_write",
    "AlphaTestEnable":"alpha_test",
    "CullingEnable":"use_backface_culling",
    "BlendMode":"blend_mode",    
},

("DefaultW3D",):{
    "ColorAmbient":"ambient_color3",
    "ColorDiffuse":"diffuse_color3",
    "ColorSpecular":"specular_color_alt",
    "Shininess":"specular_intensity_alt",
    "ColorEmissive":"emission_color",
    "EmissiveHDRMultipler":"emission_mult",
    "Opacity":"alpha",
    "EdgeFadeOut":"edge_fade_out",
    "NumTextures":"num_textures",
    "Texture_0":"texture_0",
    "Texture_1":"texture_1",
    "UseRecolorColors":"use_recolor",
    "HouseColorPulse":"house_color_pulse",
    "UseWorldCords":"use_world",
    "DepthWriteEnable":"depth_write",
    "AlphaTestEnable":"alpha_test",
    "CullingEnable":"use_backface_culling",
    "BlendMode":"blend_mode",
    "SecondaryTextureBlendMode":"secondary_texture_blend_mode",
    "TexCoordMapper_0":"tex_coord_mapper_0",
    "TexCoordTransform_0":"tex_coord_transform_0",
    "TextureAnimation_FPS_NumPerRow_LastFrame_FrameOffset_0":"tex_ani_fps_NPR_lastFrame_frameOffset_0",
    "TexCoordMapper_1":"tex_coord_mapper_1",
    "TexCoordTransform_1":"tex_coord_transform_1",

    "__Preview": "preview_scrolling_trigger"
},

("Simple",):{
    "ColorEmissive": "emission_color",
    "Texture_0":"texture_0",
    "TexCoordTransform_0": "tex_coord_transform_0",
    "DepthWriteEnable":"depth_write",
    "AlphaBlendingEnable": "alpha_blend",
    "FogEnable": "fog_enable"
},

("Simplest",):{
    "BaseTexture": "diffuse_texture"
},

("TreeSway",):{
    "DiffuseTexture":"diffuse_texture",
    "AmbientColor":"ambient_color3",
    "DiffuseColor":"diffuse_color4",
    "AlphaTestEnable":"alpha_test",
    "SwayEnable":"sway_enable",
    "Amp1":"sway_amp",
    "Freq1":"sway_freq",
    "Phase1":"sway_phase",

    "__Preview": "preview_sway_trigger",
},

("MuzzleFlash",):{
    "ColorEmissive": "emission_color",
    "Texture_0":"texture_0",
    "MultiTextureEnable": "multi_texture_enable",
    "TexCoordTransformAngle_0": "tex_coord_trans_angle",
    "TexCoordTransformU_0": "tex_coord_trans_u0",
    "TexCoordTransformV_0": "tex_coord_trans_v0",
    "TexCoordTransformU_1": "tex_coord_trans_u1",
    "TexCoordTransformV_1": "tex_coord_trans_v1",
    "TexCoordTransformU_2": "tex_coord_trans_u2",
    "TexCoordTransformV_2": "tex_coord_trans_v2",

    "__Preview": "preview_scrolling_trigger",
},


("FXLightning","FXProtonCollider"):{
    "Texture_0":"texture_0",
    "ColorDiffuse":"diffuse_color3",
    "EmissiveHDRMultipler":"emission_mult",
    "MultiTextureEnable": "multi_texture_enable",
    "DiffuseCoordOffset": "diffuse_coord_offset",
    "MultiplyBlendEnable":"multiply_blend_enable",
    "EdgeFadeOut":"edge_fade_out",
    "Texture_1":"texture_1",
    "UniqueWorldCoordEnable":"use_world",
    "UniqueWorldCoordScalar":"unique_coord_scalar",
    "UniqueWorldCoordStrength":"unique_coord_strength",
    "DisplaceScalar":"disp_scalar",
    "DisplaceAmp":"disp_amp",
    "DisplaceDivergenceAngle":"disp_angle",
    "DisplaceSpeed":"disp_speed",
    "UseRecolorColors":"use_recolor",
    "CullingEnable":"use_backface_culling",

    "__Preview": "preview_scrolling_trigger",
},

("Lightning",):{
    "Texture_0":"texture_0",
    "ColorDiffuse":"diffuse_color3",
    "HDRMultiplier":"emission_mult",
    "MultiTextureEnable": "multi_texture_enable",
    "DiffuseCoordOffset": "diffuse_coord_offset",
    "MultiplyBlendEnable":"multiply_blend_enable",
    "EdgeFadeOut":"edge_fade_out",
    "Texture_1":"texture_1",
    "UniqueWorldCoordEnable":"use_world",
    "UniqueWorldCoordScalar":"unique_coord_scalar",
    "UniqueWorldCoordStrength":"unique_coord_strength",
    "DisplaceScalar":"disp_scalar",
    "DisplaceAmp":"disp_amp",
    "DisplaceDivergenceAngle":"disp_angle",
    "DisplaceSpeed":"disp_speed",
    "UseRecolorColors":"use_recolor",
    "CullingEnable":"use_backface_culling",

    "__Preview": "preview_scrolling_trigger",
},

("DistortingObject", ):{
    "NormalMap":"normal_texture",
    "TexCoordTransform_0": "tex_coord_transform_0",
    "BumpScale":"bump_uv_scale",
    "AlphaTestEnable":"alpha_test",
},

("VERTEX_MATERIAL",):{}
}


material_compatible_map = {
    ("ObjectsGDI","ObjectsAlien","ObjectsHuman","ObjectsNOD", "cnc4_object_nod_infantry","cnc4_object_nod","cnc4_object_gdi"):"ObjectsAllied",
    ("ObjectsGenericEnvMap", "cnc4_object", "cnc4_debris_fadeoff"):"ObjectsGeneric",
    ("cnc4_object_gdi_proceduraldamage","cnc4_object_nod_proceduraldamage","cnc4_object_proceduraldamage"):"BuildingsGenericDamageFill",
    ("cnc4_vfx",) : "DefaultW3D"
}


def get_material_parameter_map(material_name, context = None):
    for keys in material_parameter_map:
        for key in keys:
            if str.upper(material_name) == str.upper(key):
                return key, material_parameter_map[keys]
            
    for keys in material_compatible_map:
        for key in keys:
            if str.upper(material_name) == str.upper(key):
                msg = f'Use compatible shader from RA3 for imported shader: "{material_name}"'
                print(msg)
                if context is not None:
                    context.info(msg)
                return get_material_parameter_map(material_compatible_map[keys])

    msg = f'shader class not in defined: {material_name}. Use DefaultW3D!'
    print(msg)
    if context is not None:
        context.error(msg)
    return "DefaultW3D", material_parameter_map[("DefaultW3D",)]

material_type_items = []
for keys in material_parameter_map:
    for key in keys:
        material_type_items.append((key, key, ''))
