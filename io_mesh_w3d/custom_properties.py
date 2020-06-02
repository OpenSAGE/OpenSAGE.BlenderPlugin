# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.props import *
from bpy.types import Panel, Object, Material, PropertyGroup, Bone

##########################################################################
# Object
##########################################################################

Object.userText = StringProperty(
    name='User Text',
    description='This is a text defined by the user',
    default='')

Object.object_type = EnumProperty(
    name='Type',
    description='Attributes that define the type of this object',
    items=[
        ('NORMAL', 'Normal', 'desc: just a normal mesh'),
        ('BOX', 'Box', 'desc: this object defines a boundingbox'),
        ('DAZZLE', 'Dazzle', 'desc: todo')],
    default='NORMAL')

Object.dazzle_type = EnumProperty(
    name='Dazzle Type',
    description='defines the dazzle type',
    items=[
        ('DEFAULT', 'default', 'desc: todo'),
        ('SUN', 'sun', 'desc: todo'),
        ('REN_L5_STREETLIGHT', 'Ren L5 streetlight', 'desc: todo'),
        ('REN_BRAKELIGHT', 'Ren brakelight', 'desc: todo'),
        ('REN_HEADLIGHT', 'Ren headlight', 'desc: todo'),
        ('REN_L5_REDLIGHT', 'Ren L5 redlight', 'desc: todo'),
        ('REN_NUKE', 'Ren nuke', 'desc: todo'),
        ('REN_BLINKLIGHT_RED', 'Ren blinklight red', 'desc: todo'),
        ('REN_BLINKLIGHT_WHITE', 'Ren blinklight white', 'desc: todo'),
        ('REN_VEHICLELIGHT_RED', 'Ren vehicle light red', 'desc: todo'),
        ('REN_VEHICLELIGHT_WHITE', 'Ren vehicle light white', 'desc: todo')],
    default='DEFAULT')


##########################################################################
# PoseBone
##########################################################################

Bone.visibility = FloatProperty(
    name='Visibility',
    default=1.0,
    min=0.0, max=1.0,
    description='Visibility property')

##########################################################################
# Material
##########################################################################


Material.material_type = EnumProperty(
    name='Material Type',
    description='defines the type of the material',
    items=[
        ('SHADER_MATERIAL', 'Shader Material', 'desc: todo'),
        ('VERTEX_MATERIAL', 'Vertex Material', 'desc: todo'),
        ('PRELIT_MATERIAL', 'Prelit Material', 'desc: todo')],
    default='VERTEX_MATERIAL')

Material.prelit_type = EnumProperty(
    name='Prelit Type',
    description='defines the prelit type of the vertex material',
    items=[
        ('PRELIT_UNLIT', 'Prelit Unlit', 'desc: todo'),
        ('PRELIT_VERTEX', 'Prelit Vertex', 'desc: todo'),
        ('PRELIT_LIGHTMAP_MULTI_PASS', 'Prelit Lightmap multi Pass', 'desc: todo'),
        ('PRELIT_LIGHTMAP_MULTI_TEXTURE', 'Prelit Lightmap multi Texture', 'desc: todo')],
    default='PRELIT_UNLIT')

Material.attributes = EnumProperty(
    name='attributes',
    description='Attributes that define the behaviour of this material',
    items=[
        ('DEFAULT', 'Default', 'desc: todo', 0),
        ('USE_DEPTH_CUE', 'UseDepthCue', 'desc: todo', 1),
        ('ARGB_EMISSIVE_ONLY', 'ArgbEmissiveOnly', 'desc: todo', 2),
        ('COPY_SPECULAR_TO_DIFFUSE', 'CopySpecularToDiffuse', 'desc: todo', 4),
        ('DEPTH_CUE_TO_ALPHA', 'DepthCueToAlpha', 'desc: todo', 8)],
    default=set(),
    options={'ENUM_FLAG'})

Material.surface_type = EnumProperty(
    name='Surface type',
    description='Describes the surface type for this material',
    items=[
        ('0', 'LightMetal', 'desc: todo'),
        ('1', 'HeavyMetal', 'desc: todo'),
        ('2', 'Water', 'desc: todo'),
        ('3', 'Sand', 'desc: todo'),
        ('4', 'Dirt', 'desc: todo'),
        ('5', 'Mud', 'desc: todo'),
        ('6', 'Grass', 'desc: todo'),
        ('7', 'Wood', 'desc: todo'),
        ('8', 'Concrete', 'desc: todo'),
        ('9', 'Flesh', 'desc: todo'),
        ('10', 'Rock', 'desc: todo'),
        ('11', 'Snow', 'desc: todo'),
        ('12', 'Ice', 'desc: todo'),
        ('13', 'Default', 'desc: todo'),
        ('14', 'Glass', 'desc: todo'),
        ('15', 'Cloth', 'desc: todo'),
        ('16', 'TiberiumField', 'desc: todo'),
        ('17', 'FoliagePermeable', 'desc: todo'),
        ('18', 'GlassPermeable', 'desc: todo'),
        ('19', 'IcePermeable', 'desc: todo'),
        ('20', 'ClothPermeable', 'desc: todo'),
        ('21', 'Electrical', 'desc: todo'),
        ('22', 'Flammable', 'desc: todo'),
        ('23', 'Steam', 'desc: todo'),
        ('24', 'ElectricalPermeable', 'desc: todo'),
        ('25', 'FlammablePermeable', 'desc: todo'),
        ('26', 'SteamPermeable', 'desc: todo'),
        ('27', 'WaterPermeable', 'desc: todo'),
        ('28', 'TiberiumWater', 'desc: todo'),
        ('29', 'TiberiumWaterPermeable', 'desc: todo'),
        ('30', 'UnderwaterDirt', 'desc: todo'),
        ('31', 'UnderwaterTiberiumDirt', 'desc: todo')],
    default='13')


Material.translucency = FloatProperty(
    name='Translucency',
    default=0.0,
    min=0.0, max=1.0,
    description='Translucency property')

Material.vm_args_0 = StringProperty(
    name='vm_args_0',
    description='Vertex Material Arguments 0',
    default='')

Material.vm_args_1 = StringProperty(
    name='vm_args_1',
    description='Vertex Material Arguments 1',
    default='')

Material.technique = IntProperty(
    name='Technique',
    description='Dont know yet',
    default=0,
    min=0,
    max=1)

Material.ambient = FloatVectorProperty(
    name='Ambient',
    subtype='COLOR',
    size=4,
    default=(1.0, 1.0, 1.0, 0.0),
    min=0.0, max=1.0,
    description='Ambient color')

Material.emission = FloatVectorProperty(
    name='Emission',
    subtype='COLOR',
    size=4,
    default=(1.0, 1.0, 1.0, 0.0),
    min=0.0, max=1.0,
    description='Emission color')

Material.alpha_test = BoolProperty(
    name='Alpha test',
    description='Enable the alpha test',
    default=True)

Material.blend_mode = IntProperty(
    name='Blend mode',
    description='Which blend mode should be used',
    default=0,
    min=0,
    max=5)

Material.bump_uv_scale = FloatVectorProperty(
    name='Bump UV Scale',
    subtype='TRANSLATION',
    size=2,
    default=(0.0, 0.0),
    min=0.0, max=1.0,
    description='Bump uv scale')

Material.edge_fade_out = IntProperty(
    name='Edge fade out',
    description='TODO',
    default=0,
    min=0,
    max=5)

Material.depth_write = BoolProperty(
    name='Depth write',
    description='Todo',
    default=False)

Material.sampler_clamp_uv_no_mip_0 = FloatVectorProperty(
    name='Sampler clamp UV no MIP 0',
    subtype='TRANSLATION',
    size=4,
    default=(0.0, 0.0, 0.0, 0.0),
    min=0.0, max=1.0,
    description='Sampler clampU clampV no mipmap 0')

Material.sampler_clamp_uv_no_mip_1 = FloatVectorProperty(
    name='Sampler clamp UV no MIP 1',
    subtype='TRANSLATION',
    size=4,
    default=(0.0, 0.0, 0.0, 0.0),
    min=0.0, max=1.0,
    description='Sampler clampU clampV no mipmap 1')

Material.num_textures = IntProperty(
    name='NumTextures',
    description='TODO',
    default=0,
    min=0,
    max=5)

Material.texture_1 = StringProperty(
    name='Texture 1',
    description='TODO',
    default='')

Material.secondary_texture_blend_mode = IntProperty(
    name='Secondary texture blend mode',
    description='TODO',
    default=0,
    min=0,
    max=5)

Material.tex_coord_mapper_0 = IntProperty(
    name='TexCoord mapper 0',
    description='TODO',
    default=0,
    min=0,
    max=5)

Material.tex_coord_mapper_1 = IntProperty(
    name='TexCoord mapper 1',
    description='TODO',
    default=0,
    min=0,
    max=5)

Material.tex_coord_transform_0 = FloatVectorProperty(
    name='TexCoord transform 0',
    subtype='TRANSLATION',
    size=4,
    default=(0.0, 0.0, 0.0, 0.0),
    min=0.0, max=1.0,
    description='TODO')

Material.tex_coord_transform_1 = FloatVectorProperty(
    name='TexCoord transform 1',
    subtype='TRANSLATION',
    size=4,
    default=(0.0, 0.0, 0.0, 0.0),
    min=0.0, max=1.0,
    description='TODO')

Material.environment_texture = StringProperty(
    name='Environment texture',
    description='TODO',
    default='')

Material.environment_mult = FloatProperty(
    name='Environment mult',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.recolor_texture = StringProperty(
    name='Recolor texture',
    description='TODO',
    default='')

Material.recolor_mult = FloatProperty(
    name='Recolor mult',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.use_recolor = BoolProperty(
    name='Use recolor colors',
    description='Todo',
    default=False)

Material.house_color_pulse = BoolProperty(
    name='House color pulse',
    description='Todo',
    default=False)

Material.scrolling_mask_texture = StringProperty(
    name='Scrolling mask texture',
    description='TODO',
    default='')

Material.tex_coord_transform_angle = FloatProperty(
    name='Texture coord transform angle',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.tex_coord_transform_u_0 = FloatProperty(
    name='Texture coord transform u 0',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.tex_coord_transform_v_0 = FloatProperty(
    name='Texture coord transform v 0',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.tex_coord_transform_u_1 = FloatProperty(
    name='Texture coord transform u 0',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.tex_coord_transform_v_1 = FloatProperty(
    name='Texture coord transform v 0',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.tex_coord_transform_u_2 = FloatProperty(
    name='Texture coord transform u 0',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.tex_coord_transform_v_2 = FloatProperty(
    name='Texture coord transform v 0',
    default=0.0,
    min=0.0, max=1.0,
    description='Todo')

Material.tex_ani_fps_NPR_lastFrame_frameOffset_0 = FloatVectorProperty(
    name='TextureAnimation FPS NumPerRow LastFrame FrameOffset 0',
    subtype='TRANSLATION',
    size=4,
    default=(0.0, 0.0, 0.0, 0.0),
    min=0.0, max=1.0,
    description='TODO')

Material.ion_hull_texture = StringProperty(
    name='Ion hull texture',
    description='TODO',
    default='')

Material.multi_texture_enable = BoolProperty(
    name='Multi texture enable',
    description='Todo',
    default=False)

##########################################################################
# Material.Shader
##########################################################################


class ShaderProperties(PropertyGroup):
    depth_compare: EnumProperty(
        name='Depth Compare',
        description='Describes how to depth check this material',
        items=[
            ('0', 'PASS_NEVER', 'pass never (i.e. always fail depth comparison test)'),
            ('1', 'PASS_LESS', 'pass if incoming less than stored'),
            ('2', 'PASS_EQUAL', 'pass if incoming equal to stored'),
            ('3', 'PASS_LEQUAL', 'pass if incoming less than or equal to stored (default)'),
            ('4', 'PASS_GREATER', 'pass if incoming greater than stored'),
            ('5', 'PASS_NOTEQUAL', 'pass if incoming not equal to stored'),
            ('6', 'PASS_GEQUAL', 'pass if incoming greater than or equal to stored'),
            ('7', 'PASS_ALWAYS', 'pass always')],
        default='3')

    depth_mask: EnumProperty(
        name='Write Depthmask',
        description='Wether or not to store the depthmask',
        items=[
            ('0', 'DISABLE', 'disable depth buffer writes'),
            ('1', 'ENABLE', 'enable depth buffer writes (default)')],
        default='1')

    color_mask: IntProperty(min=0, max=255, name='Color Mask')
    dest_blend: EnumProperty(
        name='Destination Blendfunc',
        description='Describes how this material blends',
        items=[
            ('0', 'Zero', 'destination pixel doesn\'t affect blending (default)'),
            ('1', 'One', 'destination pixel added unmodified'),
            ('2', 'SrcColor', 'destination pixel multiplied by fragment RGB components'),
            ('3', 'OneMinusSrcColor',
             'destination pixel multiplied by one minus (i.e. inverse) fragment RGB components'),
            ('4', 'SrcAlpha', 'destination pixel multiplied by fragment alpha component'),
            ('5', 'OneMinusSrcAlpha',
             'destination pixel multiplied by one minus (i.e. inverse) fragment alpha component'),
            ('6', 'SrcColorPreFog',
             'destination pixel multiplied by fragment RGB components prior to fogging'),
        ],
        default='0')
    fog_func: IntProperty(min=0, max=255, name='Fog function')

    pri_gradient: EnumProperty(
        name='Primary Gradient',
        description='Specify the primary gradient',
        items=[
            ('0', 'Disable', 'disable primary gradient (same as OpenGL \'decal\' texture blend)'),
            ('1', 'Modulate', 'modulate fragment ARGB by gradient ARGB (default)'),
            ('2', 'Add', 'add gradient RGB to fragment RGB, copy gradient A to fragment A'),
            ('3', 'BumpEnvMap', 'environment-mapped bump mapping'),
            ('5', 'Enable', '')],
        default='1')

    sec_gradient: EnumProperty(
        name='Secondary Gradient',
        description='Specify the primary gradient',
        items=[
            ('0', 'Disable', 'don\'t draw secondary gradient (default)'),
            ('1', 'Enable', 'add secondary gradient RGB to fragment RGB')],
        default='0')

    src_blend: EnumProperty(
        name='Source Blendfunc',
        description='Describes how this material blends',
        items=[
            ('0', 'Zero', 'fragment not added to color buffer'),
            ('1', 'One', 'fragment added unmodified to color buffer (default)'),
            ('2', 'SrcAlpha', 'fragment RGB components multiplied by fragment A'),
            ('3', 'OneMinusSrcAlpha',
             'fragment RGB components multiplied by fragment inverse (one minus) A'),
        ],
        default='1')
    texturing: EnumProperty(
        name='Shader texturing',
        description='Enable texturing',
        items=[
            ('0', 'Disable', 'no texturing (treat fragment initial color as 1,1,1,1) (default)'),
            ('1', 'Enable', 'enable texturing'),
        ],
        default='0')
    detail_color_func: EnumProperty(
        name='Detail color function',
        items=[
            ('0', 'Disable', 'local (default)'),
            ('1', 'Detail', 'other'),
            ('2', 'Scale', 'local * other'),
            ('3', 'InvScale', '~(~local * ~other) = local + (1-local)*other'),
            ('4', 'Add', 'local + other'),
            ('5', 'Sub', 'local - other'),
            ('6', 'SubR', 'other - local'),
            ('7', 'Blend', '(localAlpha)*local + (~localAlpha)*other'),
            ('8', 'DetailBlend', '(otherAlpha)*local + (~otherAlpha)*other'),
            ('9', 'Alt', ''),
            ('10', 'DetailAlt', ''),
            ('11', 'ScaleAlt', ''),
            ('12', 'InvScaleAlt', ''),
        ],
        default='0')
    detail_alpha_func: EnumProperty(
        name='Detail alpha function',
        items=[
            ('0', 'Disable', 'local (default)'),
            ('1', 'Detail', 'other'),
            ('2', 'Scale', 'local * other'),
            ('3', 'InvScale', '~(~local * ~other) = local + (1-local)*other'),
        ],
        default='0')
    shader_preset: bpy.props.IntProperty(min=0, max=255, name="Shader presets")
    alpha_test: EnumProperty(
        name='Alpha test',
        description='Specify wether or not to alpha check',
        items=[
            ('0', 'Disable', 'disable alpha testing (default)'),
            ('1', 'Enable', 'enable alpha testing')],
        default='0')
    post_detail_color_func: EnumProperty(
        name='Post-Detail color function',
        items=[
            ('0', 'Disable', 'local (default)'),
            ('1', 'Detail', 'other'),
            ('2', 'Scale', 'local * other'),
            ('3', 'InvScale', '~(~local * ~other) = local + (1-local)*other'),
            ('4', 'Add', 'local + other'),
            ('5', 'Sub', 'local - other'),
            ('6', 'SubR', 'other - local'),
            ('7', 'Blend', '(localAlpha)*local + (~localAlpha)*other'),
            ('8', 'DetailBlend', '(otherAlpha)*local + (~otherAlpha)*other'),
            ('9', 'Alt', ''),
            ('10', 'DetailAlt', ''),
            ('11', 'ScaleAlt', ''),
            ('12', 'InvScaleAlt', ''),
        ],
        default='0')
    post_detail_alpha_func: EnumProperty(
        name='Post-Detail alpha function',
        items=[
            ('0', 'Disable', 'local (default)'),
            ('1', 'Detail', 'other'),
            ('2', 'Scale', 'local * other'),
            ('3', 'InvScale', '~(~local * ~other) = local + (1-local)*other'),
        ],
        default='0')
