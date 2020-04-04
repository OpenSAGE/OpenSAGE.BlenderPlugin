# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.node_groups.helpers import *


class NormalMappedGroup():
    name = 'NormalMapped.fx'

    @staticmethod
    def apply_data(context, node_tree, instance, shader_mat, uv_layer):
        links = node_tree.links

        if shader_mat.header.technique is not None:
            instance.inputs['Technique'].default_value = shader_mat.header.technique

        for prop in shader_mat.properties:
            if prop.name in ['DiffuseTexture', 'Texture_0'] and prop.value != '':
                texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
                texture_node.location = (-550, 600)
                links.new(texture_node.outputs['Color'], instance.inputs['DiffuseTexture'])
                links.new(texture_node.outputs['Alpha'], instance.inputs['DiffuseTextureAlpha'])
                uv_node = create_uv_map_node(node_tree)
                uv_node.uv_map = uv_layer
                uv_node.location = (-750, 600)
                links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])

            elif prop.name == 'NormalMap' and prop.value != '':
                texture_node = create_texture_node(node_tree, find_texture(context, prop.value))
                texture_node.location = (-550, -300)
                links.new(texture_node.outputs['Color'], instance.inputs['NormalMap'])
                links.new(texture_node.outputs['Alpha'], instance.inputs['NormalMapStrength'])
                uv_node = create_uv_map_node(node_tree)
                uv_node.uv_map = uv_layer
                uv_node.location = (-750, -300)
                links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])

            elif prop.name in ['DiffuseColor', 'ColorDiffuse']:
                instance.inputs['Diffuse'].default_value = prop.to_rgba()
            elif prop.name in ['AmbientColor', 'ColorAmbient']:
                instance.inputs['Ambient'].default_value = prop.to_rgba()
            elif prop.name in ['SpecularColor', 'ColorSpecular']:
                instance.inputs['Specular'].default_value = prop.to_rgba()
            elif prop.name in ['SpecularExponent', 'BumpScale', 'AlphaTestEnable']:
                instance.inputs[prop.name].default_value = prop.value
            else:
                context.warning(prop.name + ' -> is not a valid input of:' + NormalMappedGroup.name)

        return instance

    @staticmethod
    def create(context, node_tree, shader_mat, uv_layer):
        instance = node_tree.nodes.new(type='ShaderNodeGroup')
        instance.node_tree = bpy.data.node_groups[NormalMappedGroup.name]
        instance.label = NormalMappedGroup.name
        instance.location = (0, 300)
        instance.width = 300

        return NormalMappedGroup.apply_data(context, node_tree, instance, shader_mat, uv_layer)