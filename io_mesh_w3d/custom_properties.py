# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.props import *
from bpy.types import Mesh, Bone, Material


##########################################################################
# Material
##########################################################################


Material.surface_type = EnumProperty(
        name="Surface type",
        description="Describes the surface type for this face",
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

##########################################################################
# Mesh
##########################################################################

Mesh.userText = StringProperty(
    name='User Text',
    description='This is a text defined by the user',
    default='')

Mesh.object_type = EnumProperty(
    name='Type',
    description='Attributes that define the type of this object',
    items=[
        ('NORMAL', 'Normal', 'desc: just a normal mesh'),
        ('BOX', 'Box', 'desc: this object defines a boundingbox'),
        ('DAZZLE', 'Dazzle', 'desc: todo')],
    default='NORMAL')

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


##########################################################################
# PoseBone
##########################################################################

Bone.visibility = FloatProperty(
    name='Visibility',
    default=1.0,
    min=0.0, max=1.0,
    description='Visibility property')
