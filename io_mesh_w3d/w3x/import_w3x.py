# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.shared.structs.animation import *
from io_mesh_w3d.shared.structs.collision_box import *
from io_mesh_w3d.shared.structs.data_context import *
from io_mesh_w3d.shared.structs.hierarchy import *
from io_mesh_w3d.shared.structs.hlod import *
from io_mesh_w3d.shared.structs.mesh import *
from io_mesh_w3d.shared.structs.mesh_structs.texture import *
from io_mesh_w3d.w3x.structs.include import *


def load_file(context, data_context, path=None):
    if path is None:
        path = context.filepath

    context.info('Loading file: ' + path)

    if not os.path.exists(path):
        context.error('file not found: ' + path)
        return data_context

    doc = minidom.parse(path)
    assets = doc.getElementsByTagName('AssetDeclaration')
    if not assets:
        return data_context

    dir = os.path.dirname(path)
    for node in assets[0].childs():
        if node.tagName == 'Includes':
            for xml_include in node.childs():
                include = Include.parse(xml_include)
                source = include.source.replace('ART:', '')
                data_context = load_file(context, data_context, os.path.join(dir, source))

        elif node.tagName == 'W3DMesh':
            data_context.meshes.append(Mesh.parse(context, node))
        elif node.tagName == 'W3DCollisionBox':
            data_context.collision_boxes.append(CollisionBox.parse(context, node))
        elif node.tagName == 'W3DContainer':
            data_context.hlod = HLod.parse(context, node)
        elif node.tagName == 'W3DHierarchy':
            data_context.hierarchy = Hierarchy.parse(context, node)
        elif node.tagName == 'W3DAnimation':
            data_context.animation = Animation.parse(context, node)
        elif node.tagName == 'Texture':
            data_context.textures.append(Texture.parse(node))
        else:
            context.warning('unsupported node ' + node.tagName + ' in file: ' + path)

    return data_context


##########################################################################
# Load
##########################################################################


def load(context, import_settings):
    data_context = DataContext(
        meshes=[],
        textures=[],
        collision_boxes=[],
        hierarchy=None,
        hlod=None)

    data_context = load_file(context, data_context)

    dir = os.path.dirname(context.filepath)
    if not data_context.meshes:
        for array in data_context.hlod.lod_arrays:
            for obj in array.sub_objects:
                path = dir + os.path.sep + obj.identifier + '.w3x'
                data_context = load_file(context, data_context, path)


    meshes = data_context.meshes
    hierarchy = data_context.hierarchy
    boxes = data_context.collision_boxes
    hlod = data_context.hlod
    animation = data_context.animation

    create_data(context, meshes, hlod, hierarchy, boxes, animation)
    return {'FINISHED'}
