# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bpy
from io_mesh_w3d.common.io_xml import *
from io_mesh_w3d.common.node_groups.helpers import *


class NodeGroupCreator():
    @staticmethod
    def create(directory, file, node_tree=None):
        path = os.path.join(directory, file)
        root = find_root(None, path)
        if root is None:
            return

        name = root.get('name')
        if name in bpy.data.node_groups and node_tree is None:
            return

        if node_tree is None:
            node_tree = bpy.data.node_groups.new(name, 'ShaderNodeTree')

        links = node_tree.links
        nodes = {}

        for xml_node in root:
            if xml_node.tag == 'include':
                file = xml_node.get('file')
                NodeGroupCreator.create(directory, file)
            elif xml_node.tag == 'parent':
                parent = xml_node.get('file')
                nodes = NodeGroupCreator.create(directory, parent, node_tree)
            elif xml_node.tag == 'node':
                type = xml_node.get('type')
                node = node_tree.nodes.new(type)
                x = float(xml_node.get('X', 0.0))
                y = float(xml_node.get('Y', 0.0))
                node.location = (x, y)
                nodes[xml_node.get('name')] = node

                for child_node in xml_node:
                    if child_node.tag != 'hide':
                        continue
                    id = child_node.get('id')
                    port_type = child_node.get('type')

                    if port_type == 'input':
                        node.inputs[id].hide = True
                    else:
                        node.outputs[id].hide = True

                if type == 'NodeGroupInput':
                    for child_node in xml_node:
                        if child_node.tag != 'input':
                            continue
                        input_type = child_node.get('type')
                        input_name = child_node.get('name')
                        node_tree.inputs.new(input_type, input_name)

                        #default = child_node.get('default')
                        #if default is not None:
                        #    if input_type == 'NodeSocketFloat':
                        #        default = float(default)
                        #    elif input_type == 'NodeSocketInt':
                        #        default = int(default)
                        #    node_tree.inputs[input_name].default_value = default

                        #min = child_node.get('min')
                        #if min is not None:
                        #    if input_type == 'NodeSocketFloat':
                        #        min = float(min)
                        #    elif input_type == 'NodeSocketInt':
                        #        min = int(min)
                        #    node_tree.inputs[input_name].min_value = min

                        #max = child_node.get('max')
                        #if max is not None:
                        #    if input_type == 'NodeSocketFloat':
                        #        max = float(max)
                        #    elif input_type == 'NodeSocketInt':
                        #        max = int(max)
                        #    node_tree.inputs[input_name].max_value = max

                elif type == 'NodeGroupOutput':
                    for child_node in xml_node:
                        if child_node.tag != 'output':
                            continue
                        output_type = child_node.get('type')
                        output_name = child_node.get('name')
                        node_tree.outputs.new(input_type, output_name)

                if type == 'ShaderNodeMath':
                    node.operation = xml_node.get('mode').upper()
                    #for child_node in xml_node:
                    #    if child_node.tag != 'input':
                    #        continue
                    #    id = child_node.get('id')
                        # TODO: support multiple input types
                    #    default = child_node.get('default')
                    #    node_tree.inputs[int(id)] = int(default)

            elif xml_node.tag == 'nodegroup':
                nodegroup = node_tree.nodes.new(type='ShaderNodeGroup')
                x = float(xml_node.get('X', 0.0))
                y = float(xml_node.get('Y', 0.0))
                nodegroup.location = (x, y)
                nodegroup.node_tree = bpy.data.node_groups[xml_node.get('type')]
                nodes[xml_node.get('name')] = nodegroup

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
        return nodes
