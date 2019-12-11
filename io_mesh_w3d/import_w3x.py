# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

import xml.dom.minidom

from io_mesh_w3d.structs_w3x.w3x_hierarchy import *


##########################################################################
# Load
##########################################################################


def load(self, context, import_settings):
    """Start the w3x import"""
    print('Loading file', self.filepath)


    mesh_structs = []
    hierarchy = None

   

    return {'FINISHED'}