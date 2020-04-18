# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.props import *
from bpy.types import Mesh, Bone, Material


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
