# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

def addInputInt(group, name, default=0, min=0, max=255):
    group.inputs.new('NodeSocketInt', name)
    group.inputs[name].default_value = default
    group.inputs[name].min_value = min
    group.inputs[name].max_value = max


def get_connected_nodes(links, node, input, types=[]):
    nodes = []
    for link in links:
        #print(link.to_node)
        #print(link.to_socket)
        if link.to_node == node and link.to_socket.identifier == input:
            # and link.from_socket in outputs:
            # and type(node) == bpy.types.ShaderNodeTexture....
            # and node.inputs[''].is_linked
            nodes.append(link.from_node)

    for node in nodes:
        print('###')
        print(node.bl_idname)
        print(node.name)
    return nodes