# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.common.node_groups.helpers import *

class AlphaPipeline():
    name = 'AlphaPipeline'

    @staticmethod
    def register():
        group = bpy.data.node_groups.new(AlphaPipeline.name, 'ShaderNodeTree')
        node_tree = group
        links = node_tree.links

        # create group inputs
        group_inputs = group.nodes.new('NodeGroupInput')
        group_inputs.location = (-500,0)
        group.inputs.new('NodeSocketColor', 'Diffuse')
        group.inputs.new('NodeSocketFloat', 'Alpha')
        group.inputs['Alpha'].default_value = 1.0
        group.inputs.new('NodeSocketInt', 'DestBlend')
        group.inputs['DestBlend'].default_value = 0
        group.inputs['DestBlend'].min_value = 0
        group.inputs['DestBlend'].max_value = 1

        # create group outputs
        group_outputs = group.nodes.new('NodeGroupOutput')
        group_outputs.location = (500,0)
        group.outputs.new('NodeSocketFloat', 'Alpha')

        # default texture alpha
        compare_1 = create_math_node(node_tree, mode='COMPARE')
        compare_1.location = (-200, 100)
        compare_1.inputs[0].default_value = 0
        links.new(group_inputs.outputs['DestBlend'], compare_1.inputs[1])
        links.new(group_inputs.outputs['Alpha'], compare_1.inputs[2])

        # v of diffuse
        seperate_hsv = create_seperate_hsv_node(node_tree)
        seperate_hsv.location = (-300, -100)
        links.new(group_inputs.outputs['Diffuse'], seperate_hsv.inputs['Color'])

        compare_2 = create_math_node(node_tree, mode='COMPARE')
        compare_2.location = (-100, -100)
        compare_2.inputs[0].default_value = 1
        links.new(group_inputs.outputs['DestBlend'], compare_2.inputs[1])
        links.new(seperate_hsv.outputs['V'], compare_2.inputs[2])

        # both
        add_node = create_math_node(node_tree, mode='ADD')
        add_node.location = (100, 0)
        links.new(compare_1.outputs['Value'], add_node.inputs[0])
        links.new(compare_2.outputs['Value'], add_node.inputs[1])

        subtract_node = create_math_node(node_tree, mode='SUBTRACT')
        subtract_node.location = (300, 0)
        subtract_node.inputs[0].default_value = 1.0
        links.new(add_node.outputs['Value'], subtract_node.inputs[1])
        links.new(subtract_node.outputs['Value'], group_outputs.inputs['Alpha'])