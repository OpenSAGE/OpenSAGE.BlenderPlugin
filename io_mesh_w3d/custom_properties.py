# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.props import *
from bpy.types import Material, PropertyGroup, Bone, Mesh, Object


#######################################################################################################################
# Mesh
#######################################################################################################################

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

Mesh.object_type = EnumProperty(
    name='Type',
    description='Attributes that define the type of this object',
    items=[
        ('MESH', 'Mesh', 'desc: just a normal mesh'),
        ('BOX', 'Box', 'desc: this object defines a boundingbox'),
        ('DAZZLE', 'Dazzle', 'desc: todo'),
        ('GEOMETRY', 'Geometry', 'desc: defines a geometry object')],
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


#######################################################################################################################
# PoseBone
#######################################################################################################################

Bone.visibility = FloatProperty(
    name='Visibility',
    default=1.0,
    min=0.0, max=1.0,
    description='Visibility property')
