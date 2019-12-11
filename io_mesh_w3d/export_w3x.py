# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bpy

from xml.dom import minidom, Node


def save(self, context, export_settings):
    """Start the w3x export and save to a .w3x file."""
    print('Saving file', self.filepath)

    export_mode = export_settings['w3d_mode']
    print("export mode: " + str(export_mode))
    
    doc = minidom.Document()

    #<?xml version="1.0" encoding="UTF-8"?>
    #<AssetDeclaration xmlns="uri:ea.com:eala:asset" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    #<Includes></Includes>

    file = open(self.filepath, "w")
    file.write(doc.toprettyxml(indent = '   '))
    file.close()

    return {'FINISHED'}
