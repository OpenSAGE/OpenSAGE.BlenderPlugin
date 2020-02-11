# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.common.structs.animation import *
from io_mesh_w3d.common.structs.collision_box import *
from io_mesh_w3d.common.structs.data_context import *
from io_mesh_w3d.common.structs.hierarchy import *
from io_mesh_w3d.common.structs.hlod import *
from io_mesh_w3d.common.structs.mesh import *
from io_mesh_w3d.common.structs.mesh_structs.texture import *
from io_mesh_w3d.w3x.structs.include import *


def load_file(context, data_context, path=None):
    if path is None:
        path = context.filepath

    context.info('Loading file: ' + path)

    if not os.path.exists(path):
        context.error('file not found: ' + path)
        return data_context

    root = find_root(context, path)
    if root is None:
        return data_context

    dir = os.path.dirname(path)
    for node in root:
        if node.tag == 'Includes':
            for xml_include in node:
                include = Include.parse(xml_include)
                source = include.source.replace('ART:', '')
                data_context = load_file(context, data_context, os.path.join(dir, source))

        elif node.tag == 'W3DMesh':
            data_context.meshes.append(Mesh.parse(context, node))
        elif node.tag == 'W3DCollisionBox':
            data_context.collision_boxes.append(CollisionBox.parse(context, node))
        elif node.tag == 'W3DContainer':
            data_context.hlod = HLod.parse(context, node)
        elif node.tag == 'W3DHierarchy':
            data_context.hierarchy = Hierarchy.parse(context, node)
        elif node.tag == 'W3DAnimation':
            data_context.animation = Animation.parse(context, node)
        elif node.tag == 'Texture':
            data_context.textures.append(Texture.parse(node))
        else:
            context.warning('unsupported node ' + node.tag + ' in file: ' + path)

    return data_context


##########################################################################
# Load
##########################################################################


def load(context, _):
    data_context = DataContext(
        meshes=[],
        textures=[],
        collision_boxes=[],
        hierarchy=None,
        hlod=None)

    data_context = load_file(context, data_context)

    dir = os.path.dirname(context.filepath) + os.path.sep

    if data_context.hlod is not None and not data_context.meshes:
        path = dir + os.path.sep + data_context.hlod.header.hierarchy_name + '.w3x'
        data_context = load_file(context, data_context, path)

        for array in data_context.hlod.lod_arrays:
            for obj in array.sub_objects:
                path = dir + obj.identifier + '.w3x'
                data_context = load_file(context, data_context, path)

    if data_context.hlod is None:
        if len(data_context.meshes) == 1:
            mesh = data_context.meshes[0]
            if mesh.container_name() != '':
                path = dir + mesh.container_name() + '.w3x'
                data_context = load_file(context, data_context, path)
        elif len(data_context.collision_boxes) == 1:
            box = data_context.collision_boxes[0]
            if box.container_name() != '':
                path = dir + box.container_name() + '.w3x'
                data_context = load_file(context, data_context, path)

    if data_context.hlod is not None and data_context.hierarchy is None:
        path = dir + data_context.hlod.hierarchy_name() + '.w3x'
        data_context = load_file(context, data_context, path)

    if data_context.animation is not None and data_context.hierarchy is None:
        path = dir + data_context.animation.header.hierarchy_name + '.w3x'
        data_context = load_file(context, data_context, path)

    meshes = data_context.meshes
    hierarchy = data_context.hierarchy
    boxes = data_context.collision_boxes
    hlod = data_context.hlod
    animation = data_context.animation

    create_data(context, meshes, hlod, hierarchy, boxes, animation)
    return {'FINISHED'}
