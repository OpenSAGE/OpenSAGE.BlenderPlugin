# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import os

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.import_utils import *

from io_mesh_w3d.shared.structs.data_context import *
from io_mesh_w3d.shared.structs.mesh import *
from io_mesh_w3d.shared.structs.hierarchy import *
from io_mesh_w3d.shared.structs.collision_box import *
from io_mesh_w3d.shared.structs.hlod import *
from io_mesh_w3d.shared.structs.animation import *
from io_mesh_w3d.shared.structs.mesh_structs.texture import *

from io_mesh_w3d.w3x.structs.include import *



def load_file(self, path, data_context):
    print('Loading file', path)

    if not os.path.exists(path):
        print("!!! file not found: " + path)
        self.report({'ERROR'}, "file not found: " + path)
        return data_context

    doc = minidom.parse(path)
    assets = doc.getElementsByTagName('AssetDeclaration')
    if not assets:
        return data_context

    dir = os.path.dirname(path)
    for node in assets[0].childs():
        if node.tagName == "Includes":
            for xml_include in node.childs():
                include = Include.parse(xml_include)
                source = include.source.replace("ART:", "")
                load_file(self, os.path.join(dir, source), data_context)

        elif node.tagName == "W3DMesh":
            data_context.meshes.append(Mesh.parse(node))
        elif node.tagName == "W3DCollisionBox":
            data_context.collision_boxes.append(CollisionBox.parse(node))
        elif node.tagName == "W3DContainer":
            data_context.hlod = HLod.parse(node)
        elif node.tagName == "W3DHierarchy":
            data_context.hierarchy = Hierarchy.parse(node)
        elif node.tagName == "W3DAnimation":
            data_context.animation = Animation.parse(node)
        elif node.tagName == "Texture":
            data_context.textures.append(Texture.parse(node))
        else:
            print("!!! unsupported node " + node.tagName + " in file: " + path)
            self.report({'WARNING'}, "!!! unsupported node " +
                        node.tagName + " in file: " + path)

    return data_context


##########################################################################
# Load
##########################################################################


def load(self, import_settings):
    data_context = DataContext(
        meshes=[],
        textures=[],
        collision_boxes=[],
        hierarchy=None,
        hlod=None)

    data_context = load_file(self, self.filepath, data_context)

    meshes = data_context.meshes
    hierarchy = data_context.hierarchy
    boxes = data_context.collision_boxes
    hlod = data_context.hlod
    animation = data_context.animation

    create_data(self, meshes, hlod, hierarchy, boxes, animation)
    return {'FINISHED'}
