# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

def get_material_shader(material):
    return material.get('shader', None)

def get_material_textures(material):
    textures = dict()

    node_tree = material.node_tree
    nodes = node_tree.nodes
    # ...

def create_texture_node(node_tree, tex_path):
    node = node_tree.nodes.new('ShaderNodeTexImage')
    node.name = 'TestTexture'

    node.color = (1, 0, 0)
    node.use_custom_color = True

    node.alpha_mode = 'CHANNEL_PACKED'

    node.image = image
    return node

def set_node_position(node, x, y):
    node.location = Vector((x * 300.0, y * -300.0))

def create_shader(name):
    shader = bpy.data.materials.new(name)
    #shader['shader'] = ??

    shader.use_nodes = True
    shader.use_backface_culling = True
    shader.shadow_method = 'CLIP'
    shader.blend_method = 'CLIP'

    node_tree = shader.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    shader_root = nodes.get('Principled BSDF')

    diffuse_tex = create_texture_node(node_tree, name)
    set_node_pos(diffuse_tex, -5, 0)

    links.new(diffuse_tex.outputs['Color'], shader_root.inputs['Base Color'])
    links.new(albedo_texture.outputs['Alpha'], shader_root.inputs['Alpha'])

    #specular

    #separate_rgb = node_tree.nodes.new(type="ShaderNodeSeparateRGB")
    #set_node_pos(separate_rgb, -4, 1)
    #links.new(material_texture.outputs['Color'], separate_rgb.inputs['Image'])
    # links.new(separate_rgb.outputs['R'], shader_root.inputs['Specular'])  # material.R used for custom mask?
    #links.new(separate_rgb.outputs['G'], shader_root.inputs['Specular'])
    #links.new(separate_rgb.outputs['B'], shader_root.inputs['Metallic'])
    #links.new(material_texture.outputs['Alpha'], shader_root.inputs['Roughness'])

    # normal

    normal_texture.image.colorspace_settings.is_data = True

    return shader