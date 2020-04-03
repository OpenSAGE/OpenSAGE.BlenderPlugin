# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel


    #node.color = (1, 0.5, 0)
    #node.use_custom_color = True
    #node.name = 'Test'
    #node.label

def addInputInt(group, name, default=0, min=0, max=255):
    group.inputs.new('NodeSocketInt', name)
    group.inputs[name].default_value = default
    group.inputs[name].min_value = min
    group.inputs[name].max_value = max


def create_specular_shader_node(node_tree):
    # inputs: Base Color, Specular, Roughness, Emissive Color, Transparency,
    #           Normal, Clear Coat, Clear Coat Radius, Clear Coat Normal, Ambient Occlusion
    # outputs: BSDF

    node = node_tree.nodes.new('ShaderNodeEeveeSpecular')
    node.label = 'Shader'
    # hide unused inputs
    node.inputs['Clear Coat'].hide = True
    node.inputs['Clear Coat Roughness'].hide = True
    node.inputs['Clear Coat Normal'].hide = True
    node.inputs['Ambient Occlusion'].hide = True
    return node

def create_texture_node(node_tree, texture):
    # inputs: Vector
    # outputs: Color, Alpha

    node = node_tree.nodes.new('ShaderNodeTexImage')
    #node.color_mapping
    #node.extension # interpolation past bounds
    node.image = texture
    #node.image_user
    #node.interpolation
    #node.projection
    #node.projection_blend
    #node.texture_mapping
    return node

def create_uv_map_node(node_tree):
    # outputs: UV

    node = node_tree.nodes.new('ShaderNodeUVMap')
    #node.uv_map = 'uvmapname'
    return node

def create_math_node(node_tree, mode='SUBTRACT'):
    # inputs: Value, Value
    # outputs: Value

    node = node_tree.nodes.new('ShaderNodeMath')
    node.operation = mode
    #node.clamp = False
    return node

def create_rgb_mix_node(node_tree):
    # inputs: Fac, Color1, Color2
    # outputs: Color

    node = node_tree.nodes.new('ShaderNodeMixRGB')
    #node.blend_type
    #node.use_alpha
    #node.use_clamp
    return node

def create_normal_map_node(node_tree):
    # inputs: Strength, Color
    # outputs: Normal

    node = node_tree.nodes.new('ShaderNodeNormalMap')
    node.space = 'TANGENT'
    #node.uv_map = 'uvmapname'
    return node

def create_seperate_hsv_node(node_tree):
    # inputs: Color
    # outputs: H, S, V

    node = node_tree.nodes.new('ShaderNodeSeparateHSV')
    return node

def create_rgb_node(node_tree):
    # outputs: Color

    node = node_tree.nodes.new('ShaderNodeRGB')
    return node

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