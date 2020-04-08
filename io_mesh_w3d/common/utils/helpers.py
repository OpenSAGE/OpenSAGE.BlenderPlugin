# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import os
from mathutils import Quaternion, Matrix
from bpy_extras.image_utils import load_image
from io_mesh_w3d.common.structs.rgba import RGBA


def make_transform_matrix(loc, rot):
    mat_loc = Matrix.Translation(loc)
    mat_rot = Quaternion(rot).to_matrix().to_4x4()
    return mat_loc @ mat_rot


def get_objects(type, object_list=None):  # MESH, ARMATURE
    if object_list is None:
        object_list = bpy.context.scene.objects
    return [obj for obj in object_list if obj.type == type]


def switch_to_pose(rig, pose):
    if rig is not None:
        rig.data.pose_position = pose
        bpy.context.view_layer.update()


def insensitive_path(path):
    # find the io_stream on unix
    directory = os.path.dirname(path)
    name = os.path.basename(path)

    for io_stream_name in os.listdir(directory):
        if io_stream_name.lower() == name.lower():
            path = os.path.join(directory, io_stream_name)
    return path


def get_collection(hlod=None, index=''):
    if hlod is not None:
        name = hlod.model_name() + index
        if name in bpy.data.collections:
            return bpy.data.collections[name]
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
        return coll
    return bpy.context.scene.collection


def link_object_to_active_scene(obj, coll):
    coll.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def rig_object(obj, hierarchy, rig, sub_object):
    obj.parent = rig
    obj.parent_type = 'ARMATURE'
    if sub_object.bone_index <= 0:
        return

    pivot = hierarchy.pivots[sub_object.bone_index]

    if pivot.name in rig.data.bones:
        obj.parent_bone = pivot.name
        obj.parent_type = 'BONE'
        return

    obj.rotation_mode = 'QUATERNION'
    obj.location = pivot.translation
    obj.rotation_quaternion = pivot.rotation

    parent_pivot = hierarchy.pivots[pivot.parent_id]

    if parent_pivot.name in bpy.data.objects:
        obj.parent_type = 'OBJECT'
        obj.parent = bpy.data.objects[parent_pivot.name]
    elif parent_pivot.name in rig.data.bones:
        obj.parent_bone = parent_pivot.name
        obj.parent_type = 'BONE'


def create_uvlayer(context, mesh, b_mesh, tris, mat_pass):
    tx_coords = None
    if mat_pass.tx_coords:
        tx_coords = mat_pass.tx_coords
    else:
        if mat_pass.tx_stages:
            tx_coords = mat_pass.tx_stages[0].tx_coords
        if len(mat_pass.tx_stages) > 1:
            context.warning('only one texture stage per material pass supported on export')

    if tx_coords is None:
        return

    uv_layer = mesh.uv_layers.new(do_init=False)
    for i, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            idx = tris[i][loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx].xy


def find_texture(context, file, name=None):
    if name is None:
        name = file

    file = file.split('.', -1)[0]
    if name in bpy.data.images:
        return bpy.data.images[name]

    path = insensitive_path(os.path.dirname(context.filepath))
    filepath = path + os.path.sep + file
    extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']
    img = None
    for extension in extensions:
        img = load_image(filepath + extension)
        if img is not None:
            context.info('loaded texture: ' + filepath + extension)
            break

    if img is None:
        context.warning('texture not found: ' + filepath + ' ' + str(extensions))
        img = bpy.data.images.new(name, width=2048, height=2048)
        img.generated_type = 'COLOR_GRID'
        img.source = 'GENERATED'

    img.name = name
    img.alpha_mode = 'STRAIGHT'
    return img


def get_color_value(context, node_tree, node, input):
    type = 'ShaderNodeRGB'
    socket = node.inputs[input]
    if not socket.is_linked:
        return RGBA(vec=socket.default_value)
    for link in socket.links:
        if link.from_node.bl_idname == type:
            return RGBA(vec=link.from_node.outputs['Color'].default_value)
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + input + ' in ' + node_tree.name + ' is not of type ' + type)
    return RGBA()


def get_uv_value(context, node_tree, node, input):
    type = 'ShaderNodeUVMap'
    socket = node.inputs[input]
    if not socket.is_linked:
        return None
    for link in socket.links:
        if link.from_node.bl_idname == type:
            return link.from_node.uv_map
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + input + ' in ' + node_tree.name + ' is not of type ' + type)
    return None

def get_texture_value(context, node_tree, socket):
    type = 'ShaderNodeTexImage'
    if not socket.is_linked:
        return (None, None)
    for link in socket.links:
        if link.from_node.bl_idname == type:
            return (link.from_node.image.name, get_uv_value(context, node_tree, link.from_node, 'Vector'))
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + input + ' in ' + node_tree.name + ' is not of type ' + type)
    return (None, None)


def get_texture_value(context, node_tree, node, input):
    socket = node.inputs[input]
    return get_texture_value(context, node_tree, socket)


def get_value(context, node_tree, node, input, cast):
    type = 'ShaderNodeValue'
    socket = node.inputs[input]
    if not socket.is_linked:
        return cast(socket.default_value)
    for link in socket.links:
        if link.from_node.bl_idname == type:
            return cast(link.from_node.outputs['Value'].default_value)
        else:
            context.error('Node ' + link.from_node.bl_idname + ' connected to ' + input + ' in ' + node_tree.name + ' is not of type ' + type)
    return cast(0)

def get_shader_node_group(context, node_tree):
    output_node = None

    for node in node_tree.nodes:
        if node.bl_idname == 'ShaderNodeOutputMaterial':
            output_node = node
            break

    if output_node is None:
        return None

    socket = output_node.inputs['Surface']
    if not socket.is_linked:
        return None

    for link in socket.links:
        if link.from_node.bl_idname == 'ShaderNodeGroup':
            return link.from_node
    # TODO: handle the default PrincipledBSDF here
    return None

def get_group_input_types(filename):
    dirname = os.path.dirname(__file__)
    directory = os.path.join(up(up(dirname)), 'node_group_templates')

    path = os.path.join(directory, filename)
    root = find_root(None, path)
    if root is None:
        return {}

    name = root.get('name')
    if name.replace('.fx', '') != filename.replace('.xml', ''):
        return {}

    links = node_tree.links
    inputs = {}

    for xml_node in root:
        if xml_node.tag == 'parent':
            parent = xml_node.get('file')
            inputs = get_group_input_types(parent)
        elif xml_node.tag == 'node':
            type = xml_node.get('type')
            if type != 'NodeGroupInput':
                continue
            
            for child_node in xml_node:
                if child_node.tag != 'input':
                    continue

                type = child_node.get('type')
                if type == 'ShaderNodeTexture':
                    default = child_node.get('default', None)
                elif type == 'ShaderNodeFloat':
                    default = child_node.get('default', 0.0)
                elif type == 'ShaderNodeVector2':
                    default = child_node.get('default', Vector((0.0, 0.0)))
                elif type == 'ShaderNodeVector':
                    default = child_node.get('default', Vector((0.0, 0.0, 0.0)))
                elif type == 'ShaderNodeVector4':
                    default = child_node.get('default', Vector((0.0, 0.0, 0.0, 0.0)))
                elif type == 'ShaderNodeInt':
                    default = child_node.get('default', 0)
                elif type == 'ShaderNodeByte':
                    default = child_node.get('default', 0)

                inputs[child_node.get('name')] = (type, default)

    return inputs