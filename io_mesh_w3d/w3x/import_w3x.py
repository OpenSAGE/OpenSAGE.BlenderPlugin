# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import os
from xml.dom import minidom

from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.import_utils import *

from io_mesh_w3d.w3x.structs.include import *
from io_mesh_w3d.w3x.structs.mesh import *
from io_mesh_w3d.w3x.structs.texture import *
from io_mesh_w3d.w3x.structs.hierarchy import *
from io_mesh_w3d.w3x.structs.collision_box import *
from io_mesh_w3d.w3x.structs.container import *


class W3X_CONTEXT():
    meshes = []
    textures = []
    hierarchy = None
    collision_boxes = []
    container = None


def load_file(self, path, w3x_context):
    print('Loading file', path)

    if not os.path.exists(path):
        print("!!! file not found: " + path)
        self.report({'ERROR'}, "file not found: " + path)
        return

    dir = os.path.dirname(path)

    doc = minidom.parse(path)
    if path.lower().endswith(".xml"):
        print(doc.toprettyxml(indent = '   '))

    includes = parse_object_list(doc, 'Includes', 'Include', Include.parse)
    for include in includes:
        source = include.source.replace("ART:", "")
        load_file(self, os.path.join(dir, source), w3x_context)

    #TODO: only ever parse objects that are immediate childs of the current node
    # since there is a texture node in xml files describing textures and one in fx shaders
    w3x_context.meshes.append(parse_objects(doc, "W3DMesh", Mesh.parse))
    w3x_context.collision_boxes.append(parse_objects(doc, "W3DCollisionBox", CollisionBox.parse))
    w3x_context.container = parse_objects(doc, "W3DContainer", Container.parse)
    w3x_context.hierarchy = parse_objects(doc, "W3DHierarchy", Hierarchy.parse)
    w3x_context.textures.append(parse_objects(doc, "Texture", Texture.parse))

##########################################################################
# Load
##########################################################################


def load(self, import_settings):
    w3x_context = W3X_CONTEXT()

    load_file(self, self.filepath, w3x_context)

    print(len(w3x_context.meshes))
    print(len(w3x_context.collision_boxes))
    print(len(w3x_context.textures))

    return {'FINISHED'}