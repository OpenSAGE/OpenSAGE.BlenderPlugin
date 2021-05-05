# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.props import *
from bpy.types import Material, PropertyGroup, Bone, Mesh, Object


##########################################################################
# Mesh
##########################################################################

Mesh.userText = StringProperty(
    name='User Text',
    description='This is a text defined by the user',
    default='')

Mesh.sort_level = IntProperty(
    name='Sorting level',
    description='Objects with higher sorting level are rendered after objects with lower levels.',
    default=0,
    min=0,
    max=32)

Mesh.casts_shadow = BoolProperty(
    name='Casts shadow',
    description='Determines if this object casts a shadow',
    default=True)

Mesh.two_sided = BoolProperty(
    name='Two sided',
    description='Determines if this objects faces are visible from front AND back',
    default=False)

Mesh.object_type = EnumProperty(
    name='Type',
    description='Attributes that define the type of this object',
    items=[
        ('MESH', 'Mesh', 'desc: just a normal mesh'),
        ('BOX', 'Box', 'desc: this object defines a boundingbox'),
        ('DAZZLE', 'Dazzle', 'desc: todo'),
        ('GEOMETRY', 'Geometry', 'desc: defines a geometry object'),
        ('BONE_VOLUME', 'Bone Volume', 'desc: defines a bone volume object')],
    default='MESH')

Mesh.dazzle_type = EnumProperty(
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

Mesh.geometry_type = EnumProperty(
    name='Geometry Type',
    description='defines the geometry type',
    items=[
        ('BOX', 'box', 'desc: box geometry'),
        ('SPHERE', 'sphere', 'desc: sphere geometry'),
        ('CYLINDER', 'cylinder', 'desc: cylinder geometry')],
    default='BOX')

Mesh.contact_points_type = EnumProperty(
    name='ContactPoints Type',
    description='defines the contact points type of this geometry',
    items=[
        ('NONE', 'none', 'desc: no geometry contact points'),
        ('VEHICLE', 'vehicle', 'desc: vehicle contact points'),
        ('STRUCTURE', 'structure', 'desc: structure contact points'),
        ('INFANTRY', 'infantry', 'desc: infantry contact points'),
        ('SQUAD_MEMBER', 'squad_member', 'desc: squad member contact points')],
    default='NONE')

Mesh.box_type = EnumProperty(
    name='Type',
    description='Attributes that define the type of this box object',
    items=[
        ('0', 'default', 'desc: todo'),
        ('1', 'Oriented', 'desc: todo'),
        ('2', 'Aligned', 'desc: todo')],
    default='0')

Mesh.box_collision_types = EnumProperty(
    name='Box Collision Types',
    description='Attributes that define the collision type of this box object',
    items=[
        ('DEFAULT', 'Default', 'desc: todo', 0),
        ('PHYSICAL', 'Physical', 'desc: physical collisions', 0x10),
        ('PROJECTILE', 'Projectile', 'desc: projectiles (rays) collide with this', 0x20),
        ('VIS', 'Vis', 'desc: vis rays collide with this mesh', 0x40),
        ('CAMERA', 'Camera', 'desc: cameras collide with this mesh', 0x80),
        ('VEHICLE', 'Vehicle', 'desc: vehicles collide with this mesh', 0x100)],
    default=set(),
    options={'ENUM_FLAG'})

Mesh.mass = IntProperty(
    name='Mass',
    description='The mass of this bone volume.',
    default=1,
    min=0,
    max=99999)

Mesh.spinniness = FloatProperty(
    name='Spinniness',
    default=0.0,
    min=0.0, max=100.0,
    description='Spinniness of this bone volume.')

Mesh.contact_tag = EnumProperty(
    name='Contact Tag',
    description='defines the contact tag type of this bone volume.',
    items=[
        ('DEBRIS', 'debris', 'desc: debris contact tag')],
    default='DEBRIS')


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

Material.stage0_mapping = EnumProperty(
    name='Stage 0 Mapping',
    description='defines the stage mapping type of this material',
    items=[
        ('0x00000000', 'UV', 'desc: todo'),
        ('0x00010000', 'Environment', 'desc: todo'),
        ('0x00020000', 'Cheap Environment', 'desc: todo'),
        ('0x00030000', 'Screen', 'desc: todo'),
        ('0x00040000', 'Linear Offset', 'desc: todo'),
        ('0x00050000', 'Silhouette', 'desc: todo'),
        ('0x00060000', 'Scale', 'desc: todo'),
        ('0x00070000', 'Grid', 'desc: todo'),
        ('0x00080000', 'Rotate', 'desc: todo'),
        ('0x00090000', 'Sine Linear Offset', 'desc: todo'),
        ('0x000A0000', 'Step Linear Offset', 'desc: todo'),
        ('0x000B0000', 'Zigzag Linear Offset', 'desc: todo'),
        ('0x000C0000', 'WS Classic Environment', 'desc: todo'),
        ('0x000D0000', 'WS Environment', 'desc: todo'),
        ('0x000E0000', 'Grid Classic Environment', 'desc: todo'),
        ('0x000F0000', 'Grid Environment', 'desc: todo'),
        ('0x00100000', 'Random', 'desc: todo'),
        ('0x00110000', 'Edge', 'desc: todo'),
        ('0x00120000', 'Bump Environment', 'desc: todo')],
    default='0x00000000')

Material.stage1_mapping = EnumProperty(
    name='Stage 1 Mapping',
    description='defines the stage mapping type of this material',
    items=[
        ('0x00000000', 'UV', 'desc: todo'),
        ('0x00000100', 'Environment', 'desc: todo'),
        ('0x00000200', 'Cheap Environment', 'desc: todo'),
        ('0x00000300', 'Screen', 'desc: todo'),
        ('0x00000400', 'Linear Offset', 'desc: todo'),
        ('0x00000500', 'Silhouette', 'desc: todo'),
        ('0x00000600', 'Scale', 'desc: todo'),
        ('0x00000700', 'Grid', 'desc: todo'),
        ('0x00000800', 'Rotate', 'desc: todo'),
        ('0x00000900', 'Sine Linear Offset', 'desc: todo'),
        ('0x00000A00', 'Step Linear Offset', 'desc: todo'),
        ('0x00000B00', 'Zigzag Linear Offset', 'desc: todo'),
        ('0x00000C00', 'WS Classic Environment', 'desc: todo'),
        ('0x00000D00', 'WS Environment', 'desc: todo'),
        ('0x00000E00', 'Grid Classic Environment', 'desc: todo'),
        ('0x00000F00', 'Grid Environment', 'desc: todo'),
        ('0x00001000', 'Random', 'desc: todo'),
        ('0x00001100', 'Edge', 'desc: todo'),
        ('0x00001200', 'Bump Environment', 'desc: todo')],
    default='0x00000000')

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

Material.specular = FloatVectorProperty(
    name='Specular',
    subtype='COLOR',
    size=3,
    default=(0.0, 0.0, 0.0),
    min=0.0, max=1.0,
    description='Specular color')

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

    shader_preset: IntProperty(min=0, max=255, name="Shader presets")

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
