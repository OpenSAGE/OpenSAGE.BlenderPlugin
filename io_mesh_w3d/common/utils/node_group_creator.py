# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bpy
from os.path import dirname as up
from io_mesh_w3d.common.io_xml import *
from io_mesh_w3d.common.node_groups.helpers import *


class NodeGroupCreator():
    @staticmethod
    def create_node_group(path):
        print(path)
        root = find_root(None, path)
        if root is None:
            print('None')
            return

        name = root.get('name')
        group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
        node_tree = group
        links = node_tree.links

        nodes = {}

        for xml_node in root:
            if xml_node.tag == 'node':
                type = xml_node.get('type')
                node = group.nodes.new(type)
                x = float(xml_node.get('X', 0.0))
                y = float(xml_node.get('Y', 0.0))
                node.location = (x, y)
                nodes[xml_node.get('name')] = node

                if type == 'NodeGroupInput':
                    for child_node in xml_node:
                        if child_node.tag != 'input':
                            continue
                        input_type = child_node.get('type')
                        input_name = child_node.get('name')
                        group.inputs.new(input_type, input_name)
                        print('created input: ' + input_name)

                        #default = child_node.get('default')
                        #if default is not None:
                        #    if input_type == 'NodeSocketFloat':
                        #        default = float(default)
                        #    elif input_type == 'NodeSocketInt':
                        #        default = int(default)
                        #    group.inputs[input_name].default_value = default

                        #min = child_node.get('min')
                        #if min is not None:
                        #    if input_type == 'NodeSocketFloat':
                        #        min = float(min)
                        #    elif input_type == 'NodeSocketInt':
                        #        min = int(min)
                        #    group.inputs[input_name].min_value = min

                        #max = child_node.get('max')
                        #if max is not None:
                        #    if input_type == 'NodeSocketFloat':
                        #        max = float(max)
                        #    elif input_type == 'NodeSocketInt':
                        #        max = int(max)
                        #    group.inputs[input_name].max_value = max

                elif type == 'NodeGroupOutput':
                    for child_node in xml_node:
                        if child_node.tag != 'output':
                            continue
                        output_type = child_node.get('type')
                        output_name = child_node.get('name')
                        group.outputs.new(input_type, output_name)
                        print('created output: ' + output_name)

                if type == 'ShaderNodeMath':
                    node.operation = xml_node.get('mode').upper()
                    #for child_node in xml_node:
                    #    if child_node.tag != 'input':
                    #        continue
                    #    id = child_node.get('id')
                        # TODO: support multiple input types
                    #    default = child_node.get('default')
                    #    node.inputs[int(id)] = int(default)

            elif xml_node.tag == 'link':
                from_data = xml_node.get('from').split('.')
                to_data = xml_node.get('to').split('.')

                from_node = nodes[from_data[0]]
                to_node = nodes[to_data[0]]

                from_port = from_data[2]
                if from_port.isdigit():
                    from_port = int(from_port)
                to_port = to_data[2]
                if to_port.isdigit():
                    to_port = int(to_port)

                print(from_data)
                print(to_data)
                
                if from_data[1] == 'inputs':
                    from_port = from_node.inputs[from_port]
                else:
                    from_port = from_node.outputs[from_port]

                if to_data[1] == 'inputs':
                    to_port = to_node.inputs[to_port]
                else:
                    to_port = to_node.outputs[to_port]

                links.new(from_port, to_port)
            else:
                print('node type: ' + xml_node.tag + ' is not supported')

    @staticmethod
    def create():
        dirname = os.path.dirname(__file__)
        directory = os.path.join(up(up(dirname)), 'node_group_templates')

        for file in os.listdir(directory):
            if file.endswith(".xml"):
                NodeGroupCreator.create_node_group(os.path.join(directory, file))

