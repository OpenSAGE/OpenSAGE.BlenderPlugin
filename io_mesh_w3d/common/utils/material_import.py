# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from ...common.utils.helpers import *
from ...w3d.structs.mesh_structs.vertex_material import *
from ...custom_properties import MATERIAL_PROPERTY_NAMES


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
            set_blend_method(material, 'CLIP')


def create_material_from_vertex_material(name, vert_mat):
    name = name + "." + vert_mat.vm_name
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        return material, principled

    material = bpy.data.materials.new(name)
    material.material_type = 'VERTEX_MATERIAL'
    enable_nodes(material)
    set_transparency_overlap(material, False)

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
    material.specular = vert_mat.vm_info.specular.to_vector_rgb()
    material.ambient = vert_mat.vm_info.ambient.to_vector_rgba()
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
    material.material_type = 'SHADER_MATERIAL'
    enable_nodes(material)
    set_transparency_overlap(material, False)

    material.technique = shader_mat.header.technique

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)

    for prop in shader_mat.properties:
        if prop.name == 'DiffuseTexture' and prop.value != '':
            principled.base_color_texture.image = find_texture(context, prop.value)
            principled.base_color_texture.image.name = prop.value
        elif prop.name == 'NormalMap' and prop.value != '':
            principled.normalmap_texture.image = find_texture(context, prop.value)
            principled.normalmap_texture.image.name = prop.value
        elif prop.name == 'BumpScale':
            principled.normalmap_strength = prop.value
        elif prop.name == 'SpecMap' and prop.value != '':
            principled.specular_texture.image = find_texture(context, prop.value)
            principled.specular_texture.image.name = prop.value
        elif prop.name == 'SpecularExponent' or prop.name == 'Shininess':
            material.specular_intensity = prop.value / 200.0
        elif prop.name == 'DiffuseColor' or prop.name == 'ColorDiffuse':
            material.diffuse_color = prop.to_rgba()
        elif prop.name == 'SpecularColor' or prop.name == 'ColorSpecular':
            material.specular_color = prop.to_rgb()
        elif prop.name == 'CullingEnable':
            material.use_backface_culling = prop.value
        elif prop.name == 'Texture_0':
            principled.base_color_texture.image = find_texture(context, prop.value)
            principled.base_color_texture.image.name = prop.value

        # all props below have no effect on shading -> custom properties for roundtrip purpose
        elif prop.name == 'AmbientColor' or prop.name == 'ColorAmbient':
            material.ambient = prop.to_rgba()
        elif prop.name == 'EmissiveColor' or prop.name == 'ColorEmissive':
            principled.emission_color = prop.to_rgb()
        elif prop.name == 'Opacity':
            principled.alpha = prop.value
        elif prop.name == 'AlphaTestEnable':
            material.alpha_test = prop.value
        elif prop.name == 'BlendMode':  # is blend_method ?
            material.blend_mode = prop.value
        elif prop.name == 'BumpUVScale':
            material.bump_uv_scale = prop.value.xy
        elif prop.name == 'EdgeFadeOut':
            material.edge_fade_out = prop.value
        elif prop.name == 'DepthWriteEnable':
            material.depth_write = prop.value
        elif prop.name == 'Sampler_ClampU_ClampV_NoMip_0':
            material.sampler_clamp_uv_no_mip_0 = prop.value
        elif prop.name == 'Sampler_ClampU_ClampV_NoMip_1':
            material.sampler_clamp_uv_no_mip_1 = prop.value
        elif prop.name == 'NumTextures':
            material.num_textures = prop.value  # is 1 if texture_0 and texture_1 are set
        elif prop.name == 'Texture_1':  # second diffuse texture
            # find texture just load the texture in blender
            # multiple diffuse textures still need to be switched by hand by the user
            find_texture(context, prop.value)
            material.texture_1 = prop.value
        elif prop.name == 'DamagedTexture':
            find_texture(context, prop.value)
            material.damaged_texture = prop.value
        elif prop.name == 'SecondaryTextureBlendMode':
            material.secondary_texture_blend_mode = prop.value
        elif prop.name == 'TexCoordMapper_0':
            material.tex_coord_mapper_0 = prop.value
        elif prop.name == 'TexCoordMapper_1':
            material.tex_coord_mapper_1 = prop.value
        elif prop.name == 'TexCoordTransform_0':
            material.tex_coord_transform_0 = prop.value
        elif prop.name == 'TexCoordTransform_1':
            material.tex_coord_transform_1 = prop.value
        elif prop.name == 'EnvironmentTexture':
            material.environment_texture = prop.value
        elif prop.name == 'EnvMult':
            material.environment_mult = prop.value
        elif prop.name == 'RecolorTexture':
            material.recolor_texture = prop.value
        elif prop.name == 'RecolorMultiplier':
            material.recolor_mult = prop.value
        elif prop.name == 'UseRecolorColors':
            material.use_recolor = prop.value
        elif prop.name == 'HouseColorPulse':
            material.house_color_pulse = prop.value
        elif prop.name == 'ScrollingMaskTexture':
            material.scrolling_mask_texture = prop.value
        elif prop.name == 'TexCoordTransformAngle_0':
            material.tex_coord_transform_angle = prop.value
        elif prop.name == 'TexCoordTransformU_0':
            material.tex_coord_transform_u_0 = prop.value
        elif prop.name == 'TexCoordTransformV_0':
            material.tex_coord_transform_v_0 = prop.value
        elif prop.name == 'TexCoordTransformU_1':
            material.tex_coord_transform_u_1 = prop.value
        elif prop.name == 'TexCoordTransformV_1':
            material.tex_coord_transform_v_1 = prop.value
        elif prop.name == 'TexCoordTransformU_2':
            material.tex_coord_transform_u_2 = prop.value
        elif prop.name == 'TexCoordTransformV_2':
            material.tex_coord_transform_v_2 = prop.value
        elif prop.name == 'TextureAnimation_FPS_NumPerRow_LastFrame_FrameOffset_0':
            material.tex_ani_fps_NPR_lastFrame_frameOffset_0 = prop.value
        elif prop.name == 'IonHullTexture':
            material.ion_hull_texture = prop.value
        elif prop.name == 'MultiTextureEnable':
            material.multi_texture_enable = prop.value
        else:
            context.error('shader property not implemented: ' + prop.name)

    return material, principled


##########################################################################
# set shader properties
##########################################################################


##########################################################################
# viewport appearance
#
# Shared by the core import operator and the BfMe tools' own import/preview paths,
# so a model looks the same regardless of which one brought it in.
##########################################################################


def flatten_materials(objects):
    """Every unique material used by the objects and their children, without recursion.

    'Object.children' walks all objects in the file on every access, so recursing
    over it is quadratic. 'children_recursive' resolves the whole subtree in one go.
    """
    seen = set()
    materials = []

    for root in objects:
        for obj in (root, *root.children_recursive):
            if obj.type != 'MESH' or obj.data is None:
                continue
            for material in obj.data.materials:
                if material is not None and material.name not in seen:
                    seen.add(material.name)
                    materials.append(material)
    return materials


def zero_specular(materials):
    """Kill the Principled BSDF specular highlight.

    W3D materials are authored without one; the shininess value the importer maps
    onto the node's specular input does not correspond to it, and leaving it in
    place makes an imported model look shinier in Blender's viewport than the game
    ever renders it.
    """
    for material in materials:
        node_tree = material.node_tree
        if node_tree is None:
            continue
        for node in node_tree.nodes:
            if node.type != 'BSDF_PRINCIPLED':
                continue
            for input_name in ('Specular IOR Level', 'IOR Level', 'Specular'):
                socket = node.inputs.get(input_name)
                if socket is not None:
                    socket.default_value = 0.0
                    break


##########################################################################
# deduplication
#
# create_material_from_vertex_material/create_material_from_shader_material key their
# lookup on '<mesh name>.<material name>', so every mesh gets its own materials even
# when several meshes reference an identical definition (common for tiled/kitbashed
# props sharing one texture). The functions below merge those after the fact by
# comparing the fully built Blender materials instead, since the shader chunk that
# also affects a material's appearance is only applied once mesh creation continues
# past the point where the material itself is created.
##########################################################################

def _hashable_value(value):
    if isinstance(value, (set, frozenset)):
        return tuple(sorted(value))
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, str):
        return value
    if hasattr(value, '__len__'):
        return tuple(_hashable_value(v) for v in value)
    return value


def _material_signature(material):
    """Signature of everything this addon writes onto a material, so two materials
    with the same signature are guaranteed to render identically.

    Every key is prefixed by which bucket it came from ('custom.', 'shader.',
    'builtin.', 'node.'), since e.g. the custom 'specular' color property and the
    Principled BSDF node's 'specular' input value have nothing to do with each other
    despite sharing a name, and both need to be compared independently.
    """
    values = []

    for prop in material.bl_rna.properties:
        # only compare properties this addon itself registers; other addons (e.g.
        # BlenderKit) may register their own runtime properties on Material, and
        # those must not block deduplication of otherwise-identical materials
        if prop.identifier in MATERIAL_PROPERTY_NAMES:
            values.append(('custom.' + prop.identifier, _hashable_value(getattr(material, prop.identifier))))

    for prop in material.shader.bl_rna.properties:
        if prop.is_runtime:
            values.append(('shader.' + prop.identifier, _hashable_value(getattr(material.shader, prop.identifier))))

    # everything above covers the custom W3D properties; the actual shading result
    # also depends on a handful of Blender builtins this addon writes directly
    values.append(('builtin.diffuse_color', _hashable_value(material.diffuse_color)))
    values.append(('builtin.specular_color', _hashable_value(material.specular_color)))
    values.append(('builtin.specular_intensity', round(material.specular_intensity, 6)))
    values.append(('builtin.use_backface_culling', material.use_backface_culling))

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
    values.append(('node.base_color', _hashable_value(principled.base_color)))
    values.append(('node.alpha', round(principled.alpha, 6)))
    values.append(('node.specular', round(principled.specular, 6)))
    values.append(('node.emission_color', _hashable_value(principled.emission_color)))
    values.append(('node.normalmap_strength', round(principled.normalmap_strength, 6)))

    for texture_slot in ('base_color_texture', 'normalmap_texture', 'specular_texture'):
        # readonly wrappers return None outright, rather than a wrapper with no image,
        # when nothing feeds that particular Principled BSDF input
        texture = getattr(principled, texture_slot)
        image = texture.image if texture is not None else None
        values.append(('node.' + texture_slot, image.name if image else None))

    values.sort()
    return tuple(values)


def deduplicate_materials(materials):
    """Merge materials that are equivalent in everything this addon writes onto them,
    keeping a single Blender material datablock per distinct definition instead of one
    per mesh that happens to use it. Returns the number of materials merged away."""
    canonical_by_signature = {}
    merged = 0

    # sorted so which of several equivalent materials survives as the canonical one
    # is deterministic, rather than depending on the iteration order of a set
    for material in sorted(materials, key=lambda mat: mat.name):
        if material is None:
            continue
        signature = _material_signature(material)
        canonical = canonical_by_signature.get(signature)
        if canonical is None:
            canonical_by_signature[signature] = material
            continue
        material.user_remap(canonical)
        bpy.data.materials.remove(material)
        merged += 1

    return merged


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
