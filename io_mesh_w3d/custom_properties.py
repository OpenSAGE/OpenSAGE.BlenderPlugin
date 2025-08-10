# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
import importlib
import bpy
from bpy.props import *
from bpy.types import Material, PropertyGroup, Bone, Mesh
from bpy_extras import node_shader_utils
from io_mesh_w3d.common.utils.helpers import *


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

if bpy.app.version >= (4, 0, 0):
    class SurfaceType(bpy.types.PropertyGroup):
        value: bpy.props.IntProperty(default=0)

    bpy.utils.register_class(SurfaceType)

    class FaceMap(bpy.types.PropertyGroup):
        name: bpy.props.StringProperty(name="Face Map Name", default="Unknown")
        value: CollectionProperty(type=SurfaceType)

    bpy.utils.register_class(FaceMap)

    Mesh.face_maps = CollectionProperty(type=FaceMap)

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

try:
    from io_mesh_w3d.selected_module import *
except:
    print("Error! Material Property Group not loaded")

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
