# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.common.node_groups.normal_mapped import *


class ObjectsGDIGroup(NormalMappedGroup):
    name = 'ObjectsGDI.fx'

    @staticmethod
    def create(context, node_tree, shader_mat, uv_layer):
        instance = node_tree.nodes.new(type='ShaderNodeGroup')
        instance.node_tree = bpy.data.node_groups[ObjectsGDIGroup.name]
        instance.label = ObjectsGDIGroup.name
        instance.location = (0, 300)
        instance.width = 300

        instance = NormalMappedGroup.apply_data(context, node_tree, instance, shader_mat, uv_layer)
        links = node_tree.links

        for prop in shader_mat.properties:
            if prop.name == 'RecolorTexture' and prop.value != '':
                texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
                texture_node.location = (-550, 600)
                links.new(texture_node.outputs['Color'], instance.inputs['RecolorTexture'])
                links.new(texture_node.outputs['Alpha'], instance.inputs['RecolorTextureAlpha'])
                uv_node = create_uv_map_node(node_tree)
                uv_node.uv_map = uv_layer
                uv_node.location = (-750, 600)
                links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
            if prop.name == 'EnvironmentTexture' and prop.value != '':
                texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
                texture_node.location = (-550, 600)
                links.new(texture_node.outputs['Color'], instance.inputs['EnvironmentTexture'])
                links.new(texture_node.outputs['Alpha'], instance.inputs['EnvironmentTextureAlpha'])
                uv_node = create_uv_map_node(node_tree)
                uv_node.uv_map = uv_layer
                uv_node.location = (-750, 600)
                links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
            elif prop.name in ['RecolorTextureAlpha', 'EnvMult']:
                instance.inputs[prop.name].default_value = prop.value
            else:
                context.warning(prop.name + ' -> is not a valid input of: ' + ObjectsGDIGroup.name)

        return instance

    @staticmethod
    def register():
        group = bpy.data.node_groups.new(ObjectsGDIGroup.name, 'ShaderNodeTree')
        NormalMappedGroup.create_inputs_and_links(group, ObjectsGDIGroup.name)

        group.inputs.new('NodeSocketColor', 'RecolorTexture')
        group.inputs.new('NodeSocketFloat', 'RecolorTextureAlpha')
        group.inputs.new('NodeSocketColor', 'EnvironmentTexture')
        group.inputs.new('NodeSocketColor', 'EnvironmentTextureAlpha')
        group.inputs.new('NodeSocketFloat', 'EnvMult')


class ObjectsAlienGroup(ObjectsGDIGroup):
    name = 'ObjectsAlien.fx'