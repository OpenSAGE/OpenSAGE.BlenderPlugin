# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bpy
from io_mesh_w3d.common.io_xml import *


class NodeGroupCreator():
    def process_input_hides(self, xml_node, node):
        for child_node in xml_node:
            if child_node.tag != 'hide':
                continue
            node_id = child_node.get('id')
            port_type = child_node.get('type')

            if port_type == 'input':
                node.inputs[node_id].hide = True
            else:
                node.outputs[node_id].hide = True

    def process_value_setups(self, xml_node, node):
        for child_node in xml_node:
            if child_node.tag != 'set':
                continue
            node_id = int(child_node.get('id'))
            value = child_node.get('value')
            socket = node.inputs[node_id]
            self.process_default_value(socket, socket.type, value)


    def process_default_value(self, socket, socket_type, default):
        if default is None:
            return
        if socket_type == 'NodeSocketFloat':
            socket.default_value = float(default)
        elif socket_type == 'NodeSocketInt':
            socket.default_value = int(default)
        elif socket_type == 'NodeSocketBool':
            socket.default_value = str(default) in ['True', 'true', '1']
        elif socket_type == 'NodeSocketColor':
            values = default.split(',')
            socket.default_value = Vector((float(values[0]), float(values[1]), float(values[2]), float(values[3])))
        else:
            print('INFO: default value for NodeSocket ' + socket_type + ' not supported')
            return


    def process_min_value(self, socket, min_value):
        if min_value is None:
            return
        if socket.type == 'FLOAT':
            min_value = float(min_value)
        elif socket.type == 'INT':
            min_value = int(min_value)
        socket.min_value = min_value


    def process_max_value(self, socket, max_value):
        if max_value is None:
            return
        if socket.type == 'FLOAT':
            max_value = float(max_value)
        elif socket.type == 'INT':
            max_value = int(max_value)
        socket.max_value = max_value


    def process_presets(self, socket, socket_type, xml_node):
        self.process_default_value(socket, socket_type, xml_node.get('default'))
        self.process_min_value(socket, xml_node.get('min'))
        self.process_max_value(socket, xml_node.get('max'))


    def create_input_node(self, node_tree, xml_node):
        for child_node in xml_node:
            if child_node.tag != 'input':
                continue
            name = child_node.get('name')
            socket_type = child_node.get('type')

            socket = node_tree.inputs.new(socket_type, name)
            self.process_presets(socket, socket_type, child_node)


    def create_output_node(self, node_tree, xml_node):
        for child_node in xml_node:
            if child_node.tag != 'output':
                continue
            node_tree.outputs.new(child_node.get('type'), child_node.get('name'))


    def create(self, directory, file, node_tree=None):
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
            location = (float(xml_node.get('X', 0.0)), float(xml_node.get('Y', 0.0)))

            if xml_node.tag == 'include':
                file = xml_node.get('file')
                NodeGroupCreator().create(directory, file)

            elif xml_node.tag == 'parent':
                parent = xml_node.get('file')
                nodes = NodeGroupCreator().create(directory, parent, node_tree)

            elif xml_node.tag == 'node':
                node_type = xml_node.get('type')
                node = node_tree.nodes.new(node_type)

                node.location = location
                nodes[xml_node.get('name')] = node

                self.process_input_hides(xml_node, node)
                self.process_value_setups(xml_node, node)

                if node_type == 'NodeGroupInput':
                    self.create_input_node(node_tree, xml_node)
                elif node_type == 'NodeGroupOutput':
                    self.create_output_node(node_tree, xml_node)
                elif node_type == 'ShaderNodeMath':
                    node.operation = xml_node.get('mode').upper()
                    for inp in xml_node:
                        name = inp.get('name', int(inp.get('id')))
                        node_type = inp.get('type')
                        socket = node.inputs[name]
                        self.process_presets(socket, node_type, inp)
                elif node_type in ['ShaderNodeEeveeSpecular', 'ShaderNodeNormalMap', 'ShaderNodeSeparateHSV']:
                    continue
                else:
                    print('shader node type: ' + node_type + ' is not yet supported')

            elif xml_node.tag == 'nodegroup':
                nodegroup = node_tree.nodes.new(type='ShaderNodeGroup')
                nodegroup.location = location
                nodegroup.node_tree = bpy.data.node_groups[xml_node.get('type')]
                nodes[xml_node.get('name')] = nodegroup

            elif xml_node.tag == 'link':
                from_node, from_port, from_input = xml_node.get('from').split('.')
                to_node, to_port, to_input = xml_node.get('to').split('.')

                if from_input.isdigit():
                    from_input = int(from_input)
                if to_input.isdigit():
                    to_input = int(to_input)

                if from_port == 'inputs':
                    from_ref = nodes[from_node].inputs[from_input]
                else:
                    from_ref = nodes[from_node].outputs[from_input]

                if to_port == 'inputs':
                    to_ref = nodes[to_node].inputs[to_input]
                else:
                    to_ref = nodes[to_node].outputs[to_input]

                links.new(from_ref, to_ref)
            else:
                print('node type: ' + xml_node.tag + ' is not supported')
        return nodes


    def unregister(self, directory, file):
        path = os.path.join(directory, file)
        root = find_root(None, path)
        if root is None:
            return

        name = root.get('name')

        if name in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups[name])
