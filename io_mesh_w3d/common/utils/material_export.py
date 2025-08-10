# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from mathutils import Vector
from io_mesh_w3d.w3d.structs.mesh_structs.shader import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *
from io_mesh_w3d.custom_properties import *
import os

DEFAULT_W3D = 'DefaultW3D.fx'


def set_texture_extension_to_tga(texture_name):
    # the engine searches for .tga by default or replaces it with .dds
    return texture_name.rsplit('.', 1)[0] + '.tga'


def append_texture_if_valid(texture, used_textures):
    if isinstance(texture, str):
        if texture != '':
            texture = set_texture_extension_to_tga(texture)
            if texture not in used_textures:
                used_textures.append(texture)
    elif texture is not None and texture.image is not None:
        texture = set_texture_extension_to_tga(texture.image.name)
        if texture not in used_textures:
            used_textures.append(texture)
    return used_textures


def get_used_textures(material, principled, used_textures):
    used_textures = append_texture_if_valid(principled.base_color_texture, used_textures)
    used_textures = append_texture_if_valid(principled.normalmap_texture, used_textures)
    used_textures = append_texture_if_valid(principled.specular_texture, used_textures)

    used_textures = append_texture_if_valid(material.texture_1, used_textures)
    used_textures = append_texture_if_valid(material.damaged_texture, used_textures)
    used_textures = append_texture_if_valid(material.environment_texture, used_textures)
    used_textures = append_texture_if_valid(material.recolor_texture, used_textures)
    used_textures = append_texture_if_valid(material.scrolling_mask_texture, used_textures)

    return used_textures

def get_used_textures_global_tree():
    used_images = []
    for material in bpy.data.materials:
        if material.node_tree: 
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE': 
                    if node.image and node.image.name != "IMG_NOT_FOUND":
                        abs_path = bpy.path.abspath(node.image.filepath)
                        if os.path.exists(abs_path):
                            used_images.append((node.image.name, abs_path))
    return used_images

def retrieve_vertex_material(material, principled):
    info = VertexMaterialInfo(
        attributes=0,
        shininess=principled.specular,
        specular=RGBA(vec=material.specular_color, a=0),
        diffuse=RGBA(vec=material.diffuse_color, a=0),
        emissive=RGBA(vec=principled.emission_color, a=0),
        ambient=RGBA(vec=material.ambient_color4),
        translucency=material.translucency,
        opacity=principled.alpha)

    if 'USE_DEPTH_CUE' in material.attributes:
        info.attributes |= USE_DEPTH_CUE
    if 'ARGB_EMISSIVE_ONLY' in material.attributes:
        info.attributes |= ARGB_EMISSIVE_ONLY
    if 'COPY_SPECULAR_TO_DIFFUSE' in material.attributes:
        info.attributes |= COPY_SPECULAR_TO_DIFFUSE
    if 'DEPTH_CUE_TO_ALPHA' in material.attributes:
        info.attributes |= DEPTH_CUE_TO_ALPHA

    info.attributes |= int(material.stage0_mapping, 16) & STAGE0_MAPPING_MASK
    info.attributes |= int(material.stage1_mapping, 16) & STAGE1_MAPPING_MASK

    vert_material = VertexMaterial(
        vm_name=material.name.split('.', 1)[-1],
        vm_info=info,
        vm_args_0=material.vm_args_0.replace(' ', '').replace(',', '\r\n'),
        vm_args_1=material.vm_args_1.replace(' ', '').replace(',', '\r\n'))

    return vert_material


def append_property(shader_mat, type, name, value, default=None):
    if value is None:
        return
    if type == 1:
        if isinstance(value, str):
            if value == '':  # default
                return
        elif value.image is None:
            return
        else:
            value = value.image.name
    elif type == 2:
        if default is None:
            default = 0.0
        if abs(value - default) < 0.01:
            return
    elif type == 3 and default is None:
        default = Vector().xy
    elif type == 5 and default is None:
        default = Vector()
    elif type == 6 and default is None:
        default = 0
    elif type == 7 and default is None:
        default = False

    if value == default:
        return
    shader_mat.properties.append(ShaderMaterialProperty(
        type=type, name=name, value=value))

# "para name"         "prop name"
# "DiffuseTexture"    "diffuse_texture"
def make_property_from_blender_property(paraname, propname, material:Material):
    prop = material.bl_rna.properties[propname]
    type = 0
    value = getattr(material, propname)
    if prop.__class__.__name__ == "StringProperty":
        type = STRING_PROPERTY
    elif prop.__class__.__name__ == "FloatProperty" or prop.__class__.__name__ == "FloatVectorProperty":
        if (not hasattr(prop, "is_array")) or (hasattr(prop, "is_array") and not getattr(prop, "is_array", False)) or (hasattr(prop, "is_array") and prop.array_length == 0):
            type = FLOAT_PROPERTY
        elif hasattr(prop, "is_array") and getattr(prop, "is_array", False):
            type = FLOAT_PROPERTY + prop.array_length - 1
            if prop.subtype == "COLOR":
                value = Vector(value)
    elif prop.__class__.__name__ == "BoolProperty":
        type = BOOL_PROPERTY
    elif prop.__class__.__name__ == "IntProperty":
        type = LONG_PROPERTY
    else:
        return None
    return ShaderMaterialProperty(type=type, name=paraname, value=value)

def to_vec(color):
    return Vector((color[0], color[1], color[2], color[3] if len(color) > 3 else 1.0))


def retrieve_shader_material(context, material:Material, principled, w3x=False):
    material_type = material.material_type
    # shadername,      {"para name"     : "prop name" }
    # "ObjectsAllied", {"DiffuseTexture": "diffuse_texture"}
    shadername, para_map = get_material_parameter_map(material_type) 
    shader_mat = ShaderMaterial(
        header=ShaderMaterialHeader(
            type_name=shadername+".fx", technique=material.technique),
        properties=[])
    
    for paraname, propname in para_map.items():
        if '__' in paraname: # skip plugin helper preperties
            continue
        prop_w3d = make_property_from_blender_property(paraname, propname, material)
        if prop_w3d is not None:
            shader_mat.properties.append(make_property_from_blender_property(paraname, propname, material))
        else:
            context.warning(f'Property "{paraname}" is not recognized and will not be written')
    return shader_mat


def retrieve_shader(material):
    return Shader(
        depth_compare=int(material.shader.depth_compare),
        depth_mask=int(material.shader.depth_mask),
        color_mask=material.shader.color_mask,
        dest_blend=int(material.shader.dest_blend),
        fog_func=material.shader.fog_func,
        pri_gradient=int(material.shader.pri_gradient),
        sec_gradient=int(material.shader.sec_gradient),
        src_blend=int(material.shader.src_blend),
        texturing=0,  # is set to 1 if textures are applied
        detail_color_func=int(material.shader.detail_color_func),
        detail_alpha_func=int(material.shader.detail_alpha_func),
        shader_preset=material.shader.shader_preset,
        alpha_test=int(material.shader.alpha_test),
        post_detail_color_func=int(material.shader.post_detail_color_func),
        post_detail_alpha_func=int(material.shader.post_detail_alpha_func))
