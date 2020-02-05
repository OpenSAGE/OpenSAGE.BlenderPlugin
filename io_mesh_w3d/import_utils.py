# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bmesh
import bpy
from bpy_extras import node_shader_utils
from bpy_extras.image_utils import load_image

from io_mesh_w3d.shared.structs.animation import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.shared.utils.hierarchy_import import *
from io_mesh_w3d.shared.utils.animation_import import *
from io_mesh_w3d.shared.utils.primitives import *



def smooth_mesh(mesh_ob, mesh):
    if mesh_ob.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for polygon in mesh.polygons:
        polygon.use_smooth = True


##########################################################################
# data creation
##########################################################################


def create_data(
        context,
        meshes,
        hlod=None,
        hierarchy=None,
        boxes=[],
        animation=None,
        compressed_animation=None,
        dazzles=[]):
    rig = None
    coll = get_collection(hlod)

    rig = get_or_create_skeleton(hlod, hierarchy, coll)

    if hlod is not None:
        current_coll = coll
        for i, lod_array in enumerate(reversed(hlod.lod_arrays)):
            if i > 0:
                current_coll = get_collection(hlod, '.' + str(i))
                # collection has no hide_set()
                current_coll.hide_viewport = True

            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        create_mesh(context, mesh, hierarchy, current_coll)

                for box in boxes:
                    if box.name() == sub_object.name:
                        create_box(box, hlod, hierarchy, rig, coll)

                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        create_dazzle(context, dazzle, hlod, hierarchy, rig, coll)

        for lod_array in reversed(hlod.lod_arrays):
            for sub_object in lod_array.sub_objects:
                for mesh in meshes:
                    if mesh.name() == sub_object.name:
                        rig_mesh(mesh, hierarchy, rig, sub_object)
                for dazzle in dazzles:
                    if dazzle.name() == sub_object.name:
                        dazzle_object = bpy.data.objects[dazzle.name()]
                        rig_object(dazzle_object, hierarchy, rig, sub_object)

    else:
        for mesh in meshes:
            create_mesh(context, mesh, hierarchy, coll)

    create_animation(context, rig, animation, hierarchy)
    create_animation(context, rig, compressed_animation, hierarchy, compressed=True)


def rig_object(object, hierarchy, rig, sub_object):
    if hierarchy is None or not sub_object or sub_object.bone_index <= 0:
        return

    pivot = hierarchy.pivots[sub_object.bone_index]

    if rig is not None and pivot.name in rig.pose.bones:
        object.parent = rig
        object.parent_bone = pivot.name
        object.parent_type = 'BONE'
        return

    object.rotation_mode = 'QUATERNION'
    object.delta_location = pivot.translation
    object.delta_rotation_quaternion = pivot.rotation

    if pivot.parent_id <= 0:
        return

    parent_pivot = hierarchy.pivots[pivot.parent_id]

    if parent_pivot.name in bpy.data.objects:
        object.parent = bpy.data.objects[parent_pivot.name]
    elif rig is not None and parent_pivot.name in rig.pose.bones:
        object.parent = rig
        object.parent_bone = parent_pivot.name
        object.parent_type = 'BONE'


##########################################################################
# mesh
##########################################################################

def create_mesh(context, mesh_struct, hierarchy, coll):
    triangles = []
    for triangle in mesh_struct.triangles:
        triangles.append(tuple(triangle.vert_ids))

    mesh = bpy.data.meshes.new(mesh_struct.name())

    mesh.from_pydata(mesh_struct.verts, [], triangles)
    mesh.update()
    mesh.validate()

    mesh_ob = bpy.data.objects.new(mesh_struct.name(), mesh)
    mesh_ob.object_type = 'NORMAL'
    mesh_ob.userText = mesh_struct.user_text
    mesh_ob.use_empty_image_alpha = True

    smooth_mesh(mesh_ob, mesh)
    link_object_to_active_scene(mesh_ob, coll)

    if mesh_struct.is_hidden():
        mesh_ob.hide_set(True)

    principleds = []

    # vertex material stuff
    name = mesh_struct.name()
    if mesh_struct.vert_materials:
        create_vertex_material(context, principleds, mesh_struct, mesh, name, triangles)

    for i, shader in enumerate(mesh_struct.shaders):
        set_shader_properties(mesh.materials[i], shader)

    # shader material stuff
    if mesh_struct.shader_materials:
        for i, shaderMat in enumerate(mesh_struct.shader_materials):
            (material, principled) = create_material_from_shader_material(
                context, mesh_struct.name(), shaderMat)
            mesh.materials.append(material)
            principleds.append(principled)

        if mesh_struct.material_passes:
            b_mesh = bmesh.new()
            b_mesh.from_mesh(mesh)

        for mat_pass in mesh_struct.material_passes:
            create_uvlayer(context, mesh, b_mesh, triangles, mat_pass)


def rig_mesh(mesh_struct, hierarchy, rig, sub_object=None):
    mesh_ob = bpy.data.objects[mesh_struct.name()]

    if hierarchy is None or not hierarchy.pivots:
        return

    if mesh_struct.is_skin():
        mesh = bpy.data.meshes[mesh_ob.name]
        for i, vert_inf in enumerate(mesh_struct.vert_infs):
            weight = vert_inf.bone_inf
            if weight < 0.01:
                weight = 1.0

            pivot = hierarchy.pivots[vert_inf.bone_idx]
            if vert_inf.bone_idx <= 0:
                bone = rig
            else:
                bone = rig.data.bones[pivot.name]
            mesh.vertices[i].co = bone.matrix_local @ mesh.vertices[i].co

            if pivot.name not in mesh_ob.vertex_groups:
                mesh_ob.vertex_groups.new(name=pivot.name)
            mesh_ob.vertex_groups[pivot.name].add(
                [i], weight, 'REPLACE')

            if vert_inf.xtra_idx > 0:
                xtra_pivot = hierarchy.pivots[vert_inf.xtra_idx]
                if xtra_pivot.name not in mesh_ob.vertex_groups:
                    mesh_ob.vertex_groups.new(name=xtra_pivot.name)
                mesh_ob.vertex_groups[xtra_pivot.name].add(
                    [i], vert_inf.xtra_inf, 'ADD')

        modifier = mesh_ob.modifiers.new(rig.name, 'ARMATURE')
        modifier.object = rig
        modifier.use_bone_envelopes = False
        modifier.use_vertex_groups = True

    else:
        rig_object(mesh_ob, hierarchy, rig, sub_object)


##########################################################################
# create material
##########################################################################

def create_vertex_material(context, principleds, struct, mesh, name, triangles):
    for vertMat in struct.vert_materials:
        (material, principled) = create_material_from_vertex_material(
            context, name, vertMat)
        mesh.materials.append(material)
        principleds.append(principled)

    if struct.material_passes:
        b_mesh = bmesh.new()
        b_mesh.from_mesh(mesh)

    for mat_pass in struct.material_passes:
        create_uvlayer(context, mesh, b_mesh, triangles, mat_pass)

        if mat_pass.tx_stages:
            tx_stage = mat_pass.tx_stages[0]
            mat_id = mat_pass.vertex_material_ids[0]
            tex_id = tx_stage.tx_ids[0]
            texture = struct.textures[tex_id]
            tex = find_texture(context, texture.file, texture.id)
            principleds[mat_id].base_color_texture.image = tex
            #principleds[mat_id].alpha_texture.image = tex


def create_material_from_vertex_material(context, name, vert_mat):
    name = name + "." + vert_mat.vm_name
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        return (material, principled)

    material = bpy.data.materials.new(name)
    material.material_type = 'VERTEX_MATERIAL'
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    atts = {'DEFAULT'}
    attributes = vert_mat.vm_info.attributes
    if attributes & USE_DEPTH_CUE:
        atts.add('USE_DEPTH_CUE')
    if attributes & ARGB_EMISSIVE_ONLY:
        atts.add('ARGB_EMISSIVE_ONLY')
    if attributes & COPY_SPECULAR_TO_DIFFUSE:
        atts.add('COPY_SPECULAR_TO_DIFFUSE')
    if attributes & DEPTH_CUE_TO_ALPHA:
        atts.add('DEPTH_CUE_TO_ALPHA')

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    principled.base_color = vert_mat.vm_info.diffuse.to_vector_rgb()
    principled.alpha = vert_mat.vm_info.opacity

    material.attributes = atts
    material.specular_intensity = vert_mat.vm_info.shininess
    material.specular_color = vert_mat.vm_info.specular.to_vector_rgb()
    material.emission = vert_mat.vm_info.emissive.to_vector_rgba()
    material.ambient = vert_mat.vm_info.ambient.to_vector_rgba()
    material.translucency = vert_mat.vm_info.translucency
    material.opacity = vert_mat.vm_info.opacity

    material.vm_args_0 = vert_mat.vm_args_0
    material.vm_args_1 = vert_mat.vm_args_1

    return (material, principled)


def create_material_from_shader_material(context, name, shader_mat):
    name = name + '.' + shader_mat.header.type_name
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        return (material, principled)

    material = bpy.data.materials.new(name)
    material.material_type = 'SHADER_MATERIAL'
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    if shader_mat.header.technique_index is not None:
        material.technique = shader_mat.header.technique_index

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)

    for prop in shader_mat.properties:
        if prop.name == 'DiffuseTexture' and prop.value != '':
            principled.base_color_texture.image = find_texture(context, prop.value)
        elif prop.name == 'NormalMap' and prop.value != '':
            principled.normalmap_texture.image = find_texture(context, prop.value)
        elif prop.name == 'BumpScale':
            principled.normalmap_strength = prop.value
        elif prop.name == 'SpecMap' and prop.value != '':
            principled.specular_texture.image = find_texture(context, prop.value)
        elif prop.name == 'SpecularExponent' or prop.name == 'Shininess':
            material.specular_intensity = prop.value
        elif prop.name == 'DiffuseColor' or prop.name == 'ColorDiffuse':
            if isinstance(prop.value, RGBA):
                material.diffuse_color = prop.value.to_vector_rgba(alpha=1.0)
            else:
                material.diffuse_color = RGBA(vec=prop.value, a=1.0).to_vector_rgba(alpha=1.0)
        elif prop.name == 'SpecularColor' or prop.name == 'ColorSpecular':
            if isinstance(prop.value, RGBA):
                material.specular_color = prop.value.to_vector_rgb()
            else:
                material.specular_color = prop.value
        elif prop.name == 'CullingEnable':
            material.use_backface_culling = prop.value

        # all props below have no effect on shading -> custom properties for roundtrip purpose
        elif prop.name == 'AmbientColor' or prop.name == 'ColorAmbient':
            if isinstance(prop.value, RGBA):
                material.ambient = prop.value.to_vector_rgba()
            else:
                material.ambient = RGBA(vec=prop.value, a=1.0).to_vector_rgba(alpha=1.0)
        elif prop.name == 'EmissiveColor' or prop.name == 'ColorEmissive':
            if isinstance(prop.value, RGBA):
                material.emission = prop.value.to_vector_rgba()
            else:
                material.emission = RGBA(vec=prop.value, a=1.0).to_vector_rgba(alpha=1.0)
        elif prop.name == 'Opacity':
            material.opacity = prop.value
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
        elif prop.name == 'Texture_0':
            principled.base_color_texture.image = find_texture(context, prop.value)
        elif prop.name == 'Texture_1':  # second diffuse texture
            material.texture_1 = prop.value
        elif prop.name == 'SecondaryTextureBlendMode':
            material.secondary_texture_blend_mode = prop.value
        elif prop.name == 'TexCoordMapper_0':
            material.tex_coord_mapper_0 = prop.value
        elif prop.name == 'TexCoordMapper_1':
            material.tex_coord_mapper_1 = prop.value
        elif prop.name == 'TexCoordTransform_0':
            material.tex_coord_transform_0 = prop.value.to_vector_rgba()
        elif prop.name == 'TexCoordTransform_1':
            material.tex_coord_transform_1 = prop.value.to_vector_rgba()
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
            material.tex_ani_fps_NPR_lastFrame_frameOffset_0 = prop.value.to_vector_rgba()
        elif prop.name == 'IonHullTexture':
            material.ion_hull_texture = prop.value
        elif prop.name == 'MultiTextureEnable':
            material.multi_texture_enable = prop.value
        else:
            context.error('shader property not implemented: ' + prop.name)

    return (material, principled)


##########################################################################
# set shader properties
##########################################################################


def set_shader_properties(material, shader):
    material.shader.depth_compare = shader.depth_compare
    material.shader.depth_mask = shader.depth_mask
    material.shader.color_mask = shader.color_mask
    material.shader.dest_blend = shader.dest_blend
    material.shader.fog_func = shader.fog_func
    material.shader.pri_gradient = shader.pri_gradient
    material.shader.sec_gradient = shader.sec_gradient
    material.shader.src_blend = shader.src_blend
    material.shader.texturing = shader.texturing
    material.shader.detail_color_func = shader.detail_color_func
    material.shader.detail_alpha_func = shader.detail_alpha_func
    material.shader.shader_preset = shader.shader_preset
    material.shader.alpha_test = shader.alpha_test
    material.shader.post_detail_color_func = shader.post_detail_color_func
    material.shader.post_detail_alpha_func = shader.post_detail_alpha_func


##########################################################################
# create uvlayer
##########################################################################


def create_uvlayer(context, mesh, b_mesh, tris, mat_pass):
    tx_coords = None
    if mat_pass.tx_coords:
        tx_coords = mat_pass.tx_coords
    else:
        if len(mat_pass.tx_stages) > 0:
            tx_coords = mat_pass.tx_stages[0].tx_coords
        if len(mat_pass.tx_stages) > 1:
            context.warning('only one texture stage per material pass supported on export')

    if not tx_coords:
        return

    uv_layer = mesh.uv_layers.new(do_init=False)
    for i, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            idx = tris[i][loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx].xy


##########################################################################
# load texture
##########################################################################

def find_texture(context, file, name=None):
    if name is None:
        name = file

    file = file.split('.', -1)[0]
    if name in bpy.data.images:
        return bpy.data.images[name]

    path = insensitive_path(os.path.dirname(context.filepath))
    filepath = path + os.path.sep + file
    extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']
    for extension in extensions:
        img = load_image(filepath + extension)
        if img is not None:
            context.info('loaded texture: ' + filepath + extension)
            break

    if img is None:
        context.warning('texture not found: ' + filepath + ' ' + str(extensions))
        img = bpy.data.images.new(name, width=2048, height=2048)
        img.generated_type = 'COLOR_GRID'
        img.source = 'GENERATED'

    img.name = name
    img.alpha_mode = 'STRAIGHT'
    return img


##########################################################################
# create basic meshes
##########################################################################


def create_dazzle(context, dazzle, hlod, hierarchy, rig, coll):
    # Todo: proper dimensions for cone
    (dazzle_mesh, dazzle_cone) = create_cone(dazzle.name())
    dazzle_cone.object_type = 'DAZZLE'
    dazzle_cone.dazzle_type = dazzle.type_name
    link_object_to_active_scene(dazzle_cone, coll)

    material = bpy.data.materials.new(dazzle.name())
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    principled.base_color = (255, 255, 255)
    principled.base_color_texture.image = find_texture(context, 'SunDazzle.tga')
    dazzle_mesh.materials.append(material)


def create_box(box, hlod, hierarchy, rig, coll):
    if box is None:
        return

    x = box.extend[0] / 2.0
    y = box.extend[1] / 2.0
    z = box.extend[2]

    verts = [(x, y, z), (-x, y, z), (-x, -y, z), (x, -y, z),
             (x, y, 0), (-x, y, 0), (-x, -y, 0), (x, -y, 0)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]

    cube = bpy.data.meshes.new(box.name())
    cube.from_pydata(verts, [], faces)
    cube.update(calc_edges=True)
    box_object = bpy.data.objects.new(box.name(), cube)
    box_object.object_type = 'BOX'
    box_object.display_type = 'WIRE'
    mat = bpy.data.materials.new(box.name() + ".Material")

    mat.diffuse_color = box.color.to_vector_rgba()
    cube.materials.append(mat)
    box_object.location = box.center
    link_object_to_active_scene(box_object, coll)

    if hierarchy is None or rig is None:
        return

    sub_objects = [
        sub_object for sub_object in hlod.lod_arrays[-1].sub_objects if sub_object.name == box.name()]
    if not sub_objects:
        return
    sub_object = sub_objects[0]
    if sub_object.bone_index == 0:
        return
    pivot = hierarchy.pivots[sub_object.bone_index]
    box_object.parent = rig
    box_object.parent_bone = pivot.name
    box_object.parent_type = 'BONE'
