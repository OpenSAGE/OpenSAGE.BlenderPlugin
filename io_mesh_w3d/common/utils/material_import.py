# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.custom_properties import *


##########################################################################
# vertex material
##########################################################################

def create_vertex_material(context, principleds, structure, mesh, b_mesh, name, triangles, mesh_ob):

    if len(structure.material_passes) == 1 and len(
            structure.textures) > 1:  # condition for multiple materials per single mesh object
        # Create the same amount of materials as textures used for this mesh
        source_mat = structure.vert_materials[0]
        for texture in structure.textures:
            source_mat.vm_name = texture.id
            (material, principled) = create_material_from_vertex_material(name, source_mat)
            mesh.materials.append(material)
            principleds.append(principled)

        create_uvlayer(context, mesh, b_mesh, triangles, structure.material_passes[0])

        # Load textures
        for tex_id, texture in enumerate(structure.textures):
            texture = structure.textures[tex_id]
            tex = find_texture(context, texture.file, texture.id)
            node_tree = mesh.materials[tex_id].node_tree
            bsdf_node = node_tree.nodes.get('Principled BSDF')
            texture_node = node_tree.nodes.new('ShaderNodeTexImage')
            texture_node.image = tex
            texture_node.location = (-350, 300)
            links = node_tree.links
            links.new(texture_node.outputs['Color'], bsdf_node.inputs['Base Color'])
            links.new(texture_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])

        # Assign material to appropriate object faces
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh_ob.data)
        bm.faces.ensure_lookup_table()
        for i, face in enumerate(bm.faces):
            if(i < len(structure.material_passes[0].tx_stages[0].tx_ids[0])):
                bm.faces[i].material_index = structure.material_passes[0].tx_stages[0].tx_ids[0][i]
            else:
                bm.faces[i].material_index = structure.material_passes[0].tx_stages[0].tx_ids[0][0]
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        for vertMat in structure.vert_materials:
            (material, principled) = create_material_from_vertex_material(name, vertMat)
            mesh.materials.append(material)
            principleds.append(principled)

        for mat_pass in structure.material_passes:
            create_uvlayer(context, mesh, b_mesh, triangles, mat_pass)

            if mat_pass.tx_stages:
                tx_stage = mat_pass.tx_stages[0]
                mat_id = mat_pass.vertex_material_ids[0]
                tex_id = tx_stage.tx_ids[0][0]
                texture = structure.textures[tex_id]
                tex = find_texture(context, texture.file, texture.id)
                node_tree = mesh.materials[tex_id].node_tree
                bsdf_node = node_tree.nodes.get('Principled BSDF')
                texture_node = node_tree.nodes.new('ShaderNodeTexImage')
                texture_node.image = tex
                texture_node.location = (-350, 300)
                links = node_tree.links
                links.new(texture_node.outputs['Color'], bsdf_node.inputs['Base Color'])
                links.new(texture_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])

    # Iterate through all materials and set their blend mode to Alpha Clip for transparency
    for material in mesh.materials:
        if material:
            material.blend_method = 'CLIP'


def create_material_from_vertex_material(name, vert_mat):
    name = name + "." + vert_mat.vm_name
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        return material, principled

    material = bpy.data.materials.new(name)
    material.material_type = 'VERTEX_MATERIAL'
    material.use_nodes = True
    material.show_transparent_back = False

    attributes = {'DEFAULT'}
    attribs = vert_mat.vm_info.attributes
    if attribs & USE_DEPTH_CUE:
        attributes.add('USE_DEPTH_CUE')
    if attribs & ARGB_EMISSIVE_ONLY:
        attributes.add('ARGB_EMISSIVE_ONLY')
    if attribs & COPY_SPECULAR_TO_DIFFUSE:
        attributes.add('COPY_SPECULAR_TO_DIFFUSE')
    if attribs & DEPTH_CUE_TO_ALPHA:
        attributes.add('DEPTH_CUE_TO_ALPHA')

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    principled.base_color = vert_mat.vm_info.diffuse.to_vector_rgb()
    principled.alpha = vert_mat.vm_info.opacity
    principled.specular = vert_mat.vm_info.shininess
    principled.emission_color = vert_mat.vm_info.emissive.to_vector_rgb()

    material.attributes = attributes
    material.specular_color = vert_mat.vm_info.specular.to_vector_rgb()
    material.ambient_color4 = vert_mat.vm_info.ambient.to_vector_rgba()
    material.translucency = vert_mat.vm_info.translucency

    material.stage0_mapping = '0x%08X' % (attribs & STAGE0_MAPPING_MASK)
    material.stage1_mapping = '0x%08X' % (attribs & STAGE1_MAPPING_MASK)

    material.vm_args_0 = vert_mat.vm_args_0.replace('\r\n', ', ')
    material.vm_args_1 = vert_mat.vm_args_1.replace('\r\n', ', ')

    return material, principled


##########################################################################
# shader material
##########################################################################

def create_material_from_shader_material(context, name, shader_mat):
    name = name + '.' + shader_mat.header.type_name
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        return material, principled
    
    material = bpy.data.materials.new(name)
    material_type = str(shader_mat.header.type_name).split('.')[0]
    name, para_map = get_material_parameter_map(material_type, context)

    material.material_type_old = name
    material.material_type = name
    material.texture_path = os.path.dirname(context.filepath)
    material.use_nodes = True
    material.show_transparent_back = False
    material.technique = shader_mat.header.technique
    material.alpha_threshold = 96 / 255
    material.use_backface_culling = True

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)

    for w3dprop in shader_mat.properties:
        if w3dprop.name in para_map and w3dprop.value is not None:
            prop_name = para_map[w3dprop.name]

            # retrieve vector length info to adjust the length
            blprop = material.bl_rna.properties[prop_name]
            if getattr(blprop, "array_length", 0) == 4:
                setattr(material, prop_name, w3dprop.to_rgba())
            elif getattr(blprop, "array_length", 0) == 3:
                setattr(material, prop_name, w3dprop.to_rgb())
            else:
                setattr(material, prop_name, w3dprop.value)

        else:
            context.warning('shader property not in list: ' + w3dprop.name)

    return material, principled


##########################################################################
# set shader properties
##########################################################################


def set_shader_properties(material, shader):
    material.shader.depth_compare = str(shader.depth_compare)
    material.shader.depth_mask = str(shader.depth_mask)
    material.shader.color_mask = shader.color_mask
    material.shader.dest_blend = str(shader.dest_blend)
    material.shader.fog_func = shader.fog_func
    material.shader.pri_gradient = str(shader.pri_gradient)
    material.shader.sec_gradient = str(shader.sec_gradient)
    material.shader.src_blend = str(shader.src_blend)
    material.shader.texturing = str(shader.texturing)
    material.shader.detail_color_func = str(shader.detail_color_func)
    material.shader.detail_alpha_func = str(shader.detail_alpha_func)
    material.shader.shader_preset = shader.shader_preset
    material.shader.alpha_test = str(shader.alpha_test)
    material.shader.post_detail_color_func = str(shader.post_detail_color_func)
    material.shader.post_detail_alpha_func = str(shader.post_detail_alpha_func)
