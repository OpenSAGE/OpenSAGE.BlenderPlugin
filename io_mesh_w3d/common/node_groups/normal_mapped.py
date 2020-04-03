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

    @staticmethod
    def create_inputs_and_links(group, name):
        node_tree = group
        node_tree.name = name
        links = node_tree.links

        # create group inputs
        group_inputs = group.nodes.new('NodeGroupInput')
        group_inputs.location = (-350,0)

        addInputInt(group, 'Technique', default=1, min=0, max=3)
        group.inputs.new('NodeSocketColor', 'Diffuse')
        group.inputs['Diffuse'].default_value = (0.8, 0.8, 0.8, 1.0)
        group.inputs.new('NodeSocketColor', 'DiffuseTexture')
        group.inputs['DiffuseTexture'].default_value = (0.8, 0.8, 0.8, 1.0)
        group.inputs.new('NodeSocketFloat', 'DiffuseTextureAlpha')
        group.inputs['DiffuseTextureAlpha'].default_value = 1.0
        addInputInt(group, 'AlphaTestEnable', max=1)
        group.inputs.new('NodeSocketColor', 'NormalMap')
        group.inputs.new('NodeSocketFloat', 'NormalMapStrength')
        group.inputs.new('NodeSocketFloat', 'BumpScale')
        group.inputs.new('NodeSocketColor', 'Ambient')
        group.inputs['Ambient'].default_value = (0.8, 0.8, 0.8, 1.0)
        group.inputs.new('NodeSocketColor', 'Specular')
        group.inputs.new('NodeSocketFloat', 'SpecularExponent')

        # create group outputs
        group_outputs = group.nodes.new('NodeGroupOutput')
        group_outputs.location = (300,0)
        group.outputs.new('NodeSocketShader', 'BSDF')

        alpha_pipeline = node_tree.nodes.new(type='ShaderNodeGroup')
        alpha_pipeline.location = (-100, 0)
        alpha_pipeline.node_tree = bpy.data.node_groups['AlphaPipeline']
        links.new(group_inputs.outputs['DiffuseTexture'], alpha_pipeline.inputs['Diffuse'])
        links.new(group_inputs.outputs['DiffuseTextureAlpha'], alpha_pipeline.inputs['Alpha'])
        links.new(group_inputs.outputs['AlphaTestEnable'], alpha_pipeline.inputs['DestBlend'])

        normal = create_normal_map_node(node_tree)
        normal.location = (-100, -200)
        links.new(group_inputs.outputs['NormalMap'], normal.inputs['Color'])
        links.new(group_inputs.outputs['NormalMapStrength'], normal.inputs['Strength'])

        shader = create_specular_shader_node(node_tree)
        shader.location = (100, 0)
        shader.inputs['Emissive Color'].hide = True

        links.new(group_inputs.outputs['DiffuseTexture'], shader.inputs['Base Color'])
        links.new(group_inputs.outputs['Specular'], shader.inputs['Specular'])
        links.new(group_inputs.outputs['SpecularExponent'], shader.inputs['Roughness'])
        links.new(alpha_pipeline.outputs['Alpha'], shader.inputs['Transparency'])
        links.new(normal.outputs['Normal'], shader.inputs['Normal'])
        links.new(shader.outputs['BSDF'], group_outputs.inputs['BSDF'])


    @staticmethod
    def register():
        group = bpy.data.node_groups.new(NormalMappedGroup.name, 'ShaderNodeTree')
        NormalMappedGroup.create_inputs_and_links(group, NormalMappedGroup.name)
