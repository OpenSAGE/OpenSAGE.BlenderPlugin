# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bpy
import bmesh
import sys

from mathutils import Vector, Matrix, Quaternion

from bpy_extras import node_shader_utils
from bpy_extras.image_utils import load_image

from io_mesh_w3d.io_binary import read_chunk_head
from io_mesh_w3d.w3d_adaptive_delta import decode

from io_mesh_w3d.structs.w3d_vertex_material import *
from io_mesh_w3d.structs.w3d_animation import *
from io_mesh_w3d.structs.w3d_mesh import *


def insensitive_path(path):
     # find the io_stream on unix
    directory = os.path.dirname(path)
    name = os.path.basename(path)

    for io_streamname in os.listdir(directory):
        if io_streamname.lower() == name.lower():
            path = os.path.join(directory, io_streamname)
    return path


def link_object_to_active_scene(obj, coll):
    coll.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def smooth_mesh(mesh):
    try:
        bpy.ops.object.mode_set(mode='OBJECT')

        for polygon in mesh.polygons:
            polygon.use_smooth = True
    except RuntimeError:
        print("incorrect context for mesh smooting")


def get_collection(hlod):
    if hlod is not None:
        coll = bpy.data.collections.new(hlod.header.model_name)
        bpy.context.collection.children.link(coll)
        return coll
    return bpy.context.collection


##########################################################################
# mesh
##########################################################################

def create_mesh(self, mesh_struct, hierarchy, coll):
    triangles = []
    for triangle in mesh_struct.triangles:
        triangles.append(tuple(triangle.vert_ids))

    mesh = bpy.data.meshes.new(mesh_struct.name())

    mesh.from_pydata(mesh_struct.verts, [], triangles)
    mesh.update()
    mesh.validate()

    smooth_mesh(mesh)

    mesh_ob = bpy.data.objects.new(mesh_struct.name(), mesh)
    link_object_to_active_scene(mesh_ob, coll)
    mesh_ob['UserText'] = mesh_struct.user_text

    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    principleds = []

    for shaderMat in mesh_struct.shader_materials:
        (material, principled) = create_material_from_shader_material(
            self, mesh_struct, shaderMat)
        mesh.materials.append(material)
        principleds.append(principled)

    vert_materials = mesh_struct.vert_materials
    material_passes = mesh_struct.material_passes
    textures = mesh_struct.textures

    if mesh_struct.has_prelit_vertex():
        vert_materials = mesh_struct.prelit_vertex.vert_materials
        material_passes = mesh_struct.prelit_vertex.material_passes
        textures = mesh_struct.prelit_vertex.textures

    for vertMat in vert_materials:
        (material, principled) = create_material_from_vertex_material(
            self, mesh_struct, vertMat)
        mesh.materials.append(material)
        principleds.append(principled)

    for mat_pass in material_passes:
        create_uvlayer(mesh, b_mesh, triangles, mat_pass)

        if mat_pass.tx_stages:
            tx_stage = mat_pass.tx_stages[0]
            mat_id = mat_pass.vertex_material_ids[0]
            tex_id = tx_stage.tx_ids[0]
            texture = textures[tex_id]
            tex = load_texture(self, texture.name)
            if tex is not None:
                principleds[mat_id].base_color_texture.image = tex

    for i, shader in enumerate(mesh_struct.shaders):
        set_shader_properties(mesh.materials[i], shader)
    return mesh


def rig_mesh(mesh_struct, mesh, hierarchy, hlod, rig):
    mesh_ob = bpy.data.objects[mesh_struct.name()]

    if hierarchy is None or not hierarchy.pivots:
        return

    if mesh_struct.is_skin():
        for i, vert_inf in enumerate(mesh_struct.vert_infs):
            weight = vert_inf.bone_inf
            if weight < 0.01:
                weight = 1.0

            pivot = hierarchy.pivots[vert_inf.bone_idx]
            bone = rig.data.bones[pivot.name]
            mesh.vertices[i].co = bone.matrix_local @ mesh.vertices[i].co

            if not pivot.name in mesh_ob.vertex_groups:
                mesh_ob.vertex_groups.new(name=pivot.name)
            mesh_ob.vertex_groups[pivot.name].add(
                [i], weight, 'REPLACE')

            if vert_inf.xtra_idx != 0:
                xtra_pivot = hierarchy.pivots[vert_inf.xtra_idx]
                if not xtra_pivot.name in mesh_ob.vertex_groups:
                    mesh_ob.vertex_groups.new(name=xtra_pivot.name)
                mesh_ob.vertex_groups[xtra_pivot.name].add(
                    [i], vert_inf.xtra_inf, 'ADD')

        modifier = mesh_ob.modifiers.new(rig.name, 'ARMATURE')
        modifier.object = rig
        modifier.use_bone_envelopes = False
        modifier.use_vertex_groups = True

    else:
        pivot = None
        sub_objects = [
            sub_object for sub_object in hlod.lod_array.sub_objects if sub_object.name() == mesh_struct.name()]
        if not sub_objects:
            return
        else:
            sub_object = sub_objects[0]
            pivot = hierarchy.pivots[sub_object.bone_index]

        mesh_ob.rotation_mode = 'QUATERNION'
        mesh_ob.delta_location = pivot.translation
        mesh_ob.delta_rotation_quaternion = pivot.rotation

        if pivot.parent_id <= 0:
            return

        parent_pivot = hierarchy.pivots[pivot.parent_id]

        if parent_pivot.name in bpy.data.objects:
            mesh_ob.parent = bpy.data.objects[parent_pivot.name]
        else:
            mesh_ob.parent = rig
            mesh_ob.parent_bone = parent_pivot.name
            mesh_ob.parent_type = 'BONE'


##########################################################################
# skeleton
##########################################################################


def get_or_create_skeleton(hlod, hierarchy, coll):
    if hlod is None or hierarchy is None:
        return None

    if hierarchy.header.name in bpy.data.objects:
        obj = bpy.data.objects[hierarchy.header.name]
        if obj.type == 'ARMATURE':
            return obj
        return None

    return create_bone_hierarchy(hierarchy, hlod.lod_array.sub_objects, coll)


def make_transform_matrix(loc, rot):
    mat_loc = Matrix.Translation(loc)
    mat_rot = Quaternion(rot).to_matrix().to_4x4()
    return mat_loc @ mat_rot


def create_rig(name, location, coll):
    basic_sphere = create_sphere()
    armature = bpy.data.armatures.new(name)
    armature.show_names = False

    rig = bpy.data.objects.new(name, armature)
    rig.location = location
    rig.rotation_mode = 'QUATERNION'
    rig.track_axis = "POS_X"
    link_object_to_active_scene(rig, coll)
    bpy.ops.object.mode_set(mode='EDIT')
    return (rig, armature)


def create_bone_hierarchy(hierarchy, sub_objects, coll):
    root = hierarchy.pivots[0]
    rig = None

    for pivot in hierarchy.pivots:
        pivot.is_bone = True

    for obj in sub_objects:
        pivot = hierarchy.pivots[obj.bone_index]
        if pivot.name == obj.name():
            pivot.is_bone = False

    for i, pivot in enumerate(hierarchy.pivots):
        childs = [child for child in hierarchy.pivots if child.parent_id == i]
        for child in childs:
            if child.is_bone:
                pivot.is_bone = True

    armature = None
    for pivot in hierarchy.pivots:
        if pivot.parent_id == -1 or not pivot.is_bone:
            continue

        if rig is None:
            (rig, armature) = create_rig(
                hierarchy.header.name, root.translation, coll)

        bone = armature.edit_bones.new(pivot.name)
        matrix = make_transform_matrix(pivot.translation, pivot.rotation)

        if pivot.parent_id > 0:
            parent_pivot = hierarchy.pivots[pivot.parent_id]
            if parent_pivot.name in armature.edit_bones:
                bone.parent = armature.edit_bones[parent_pivot.name]
            else:
                print(parent_pivot.name)
            matrix = bone.parent.matrix @ matrix

        bone.head = Vector((0.0, 0.0, 0.0))
        # has to point in y direction, so rotation is applied correctly
        bone.tail = Vector((0.0, 0.01, 0.0))
        bone.matrix = matrix

    if rig is not None:
        bpy.ops.object.mode_set(mode='POSE')
        basic_sphere = create_sphere()

        for bone in rig.pose.bones:
            bone.custom_shape = basic_sphere

    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


##########################################################################
# create material
##########################################################################


def create_material_from_vertex_material(self, mesh, vert_mat):
    material = bpy.data.materials.new(
        mesh.name() + "." + vert_mat.vm_name)
    material.use_nodes = True
    #material.blend_method = 'BLEND'

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

    material.attributes = atts
    material.specular_intensity = vert_mat.vm_info.shininess
    material.specular_color = vert_mat.vm_info.specular.to_vector_rgb()
    material.diffuse_color = vert_mat.vm_info.diffuse.to_vector_rgba(alpha=1.0)

    material.emission = vert_mat.vm_info.emissive.to_vector_rgba(alpha=1.0)
    material.ambient = vert_mat.vm_info.ambient.to_vector_rgba(alpha=1.0)
    material.translucency = vert_mat.vm_info.translucency
    material.opacity = vert_mat.vm_info.opacity

    material.vm_args_0 = vert_mat.vm_args_0
    material.vm_args_1 = vert_mat.vm_args_1

    principled = create_principled_bsdf(
        self, material=material, base_color=vert_mat.vm_info.diffuse.to_vector_rgb(),
        alpha=vert_mat.vm_info.opacity)
    return (material, principled)


def create_material_from_shader_material(self, mesh, shader_mat):
    material = bpy.data.materials.new(
        mesh.name() + ".ShaderMaterial")
    material.use_nodes = True
    diffuse = None
    normal = None
    bump_scale = 0
    for prop in shader_mat.properties:
        if prop.name == "DiffuseTexture":
            diffuse = prop.value
        elif prop.name == "NormalMap":
            normal = prop.value
        elif prop.name == "BumpScale":
            bump_scale = prop.value
        elif prop.name == "SpecularExponent":
            material.specular_intensity = prop.value
        elif prop.name == "AmbientColor":
            material.ambient = prop.value.to_vector_rgba()
        elif prop.name == "DiffuseColor":
            material.diffuse_color = prop.value.to_vector_rgba()
        elif prop.name == "SpecularColor":
            material.specular_color = prop.value.to_vector_rgb()
        elif prop.name == "AlphaTestEnable":
            material.alpha_test = bool(prop.value)
        elif prop.name == "BlendMode":
            material.blend_mode = prop.value
        elif prop.name == "BumpUVScale":
            material.bump_uv_scale = prop.value.xy
        elif prop.name == "Sampler_ClampU_ClampV_NoMip_0":
            material.sampler_clamp_uv_no_mip = prop.value
        else:
            print("!!! shader property not implemented: " + prop.name)
            self.report(
                {'ERROR'}, "shader property not implemented: " + prop.name)

    principled = create_principled_bsdf(self, material=material, diffuse_tex=diffuse,
                                        normal_tex=normal, bump_scale=bump_scale)
    return (material, principled)


def create_principled_bsdf(
        self,
        material,
        base_color=None,
        alpha=0,
        diffuse_tex=None,
        normal_tex=None,
        bump_scale=0):
    principled = node_shader_utils.PrincipledBSDFWrapper(
        material, is_readonly=False)
    if base_color is not None:
        principled.base_color = base_color
    if alpha > 0:
        principled.alpha = alpha
    if diffuse_tex is not None:
        tex = load_texture(self, diffuse_tex)
        if tex is not None:
            principled.base_color_texture.image = tex
    if normal_tex is not None:
        tex = load_texture(self, normal_tex)
        if tex is not None:
            principled.normalmap_texture.image = tex
            principled.normalmap_strength = bump_scale
    return principled


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


def create_uvlayer(mesh, b_mesh, tris, mat_pass):
    tx_coords = None
    if mat_pass.tx_coords:
        tx_coords = mat_pass.tx_coords
    else:
        if len(mat_pass.tx_stages) > 0:
            tx_coords = mat_pass.tx_stages[0].tx_coords
        if len(mat_pass.tx_stages) > 1:
            print(
                "Warning!: only one texture stage per material pass supported on export")

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

def load_texture(self, tex_name):
    if tex_name is None:
        return None
    found_img = False
    basename = os.path.splitext(tex_name)[0]

    # Test if the image file already exists
    for image in bpy.data.images:
        if basename.lower() == os.path.splitext(image.name)[0].lower():
            img = image
            found_img = True

    # Try to load the image file
    if not found_img:
        tgapath = os.path.dirname(self.filepath) + "/" + basename + ".tga"
        ddspath = os.path.dirname(self.filepath) + "/" + basename + ".dds"
        tgapath = insensitive_path(tgapath)
        ddspath = insensitive_path(ddspath)

        img = load_image(tgapath)

        if img is None:
            img = load_image(ddspath)

        if img is None:
            print("missing texture:" + ddspath)
    return img


##########################################################################
# createAnimation
##########################################################################


def is_roottransform(channel):
    return channel.pivot == 0


def is_translation(channel):
    return channel.type < 3


def is_rotation(channel):
    return channel.type == 6


def is_visibility(channel):
    return isinstance(channel, AnimationBitChannel)


def get_bone(rig, hierarchy, channel):
    if is_roottransform(channel):
        return rig

    pivot = hierarchy.pivots[channel.pivot]
    if rig is not None and pivot.name in rig.pose.bones:
        return rig.pose.bones[pivot.name]
    return bpy.data.objects[pivot.name]


def setup_animation(animation):
    bpy.context.scene.render.fps = animation.header.frame_rate
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = animation.header.num_frames - 1


creation_options = {'INSERTKEY_NEEDED'}


def set_translation(bone, index, frame, value):
    bone.location[index] = value
    bone.keyframe_insert(data_path='location', index=index,
                         frame=frame, options=creation_options)


def set_rotation(bone, frame, value):
    bone.rotation_quaternion = value
    bone.keyframe_insert(data_path='rotation_quaternion',
                         frame=frame, options=creation_options)


def set_visibility(bone, frame, value):
    if isinstance(bone, bpy.types.PoseBone):
        bone.bone.hide = value
        bone.bone.keyframe_insert(
            data_path='hide', frame=frame, options=creation_options)
    else:
        bone.hide_viewport = value
        bone.keyframe_insert(data_path='hide_viewport',
                             frame=frame, options=creation_options)


def set_keyframe(bone, channel, frame, value):
    if is_visibility(channel):
        set_visibility(bone, frame, value)
    elif is_translation(channel):
        set_translation(bone, channel.type, frame, value)
    elif is_rotation(channel):
        set_rotation(bone, frame, value)


def set_visibility(bone, frame, value):
    try:
        bone.hide_viewport = value
        bone.keyframe_insert(data_path='hide_viewport', frame=frame)
    except:
        try:
            bone.bone.hide = value
            bone.bone.keyframe_insert(data_path='hide', frame=frame)
        except:
            print("Warning: " + str(bone.name) +
                  " does not support visibility bit channels")


def apply_timecoded(bone, channel, _):
    for key in channel.time_codes:
        set_keyframe(bone, channel, key.time_code, key.value)


def apply_motion_channel_time_coded(bone, channel):
    for dat in channel.data:
        set_keyframe(bone, channel, dat.time_code, dat.value)


def apply_adaptive_delta(bone, channel):
    data = decode(channel)
    for i in range(channel.num_time_codes):
        set_keyframe(bone, channel, i, data[i])


def apply_uncompressed(bone, channel, hierarchy):
    for index in range(channel.last_frame - channel.first_frame + 1):
        data = channel.data[index]
        frame = index + channel.first_frame
        set_keyframe(bone, channel, frame, data)


def process_channels(hierarchy, channels, rig, apply_func):
    for channel in channels:
        obj = get_bone(rig, hierarchy, channel)

        apply_func(obj, channel, hierarchy)


def process_motion_channels(hierarchy, channels, rig):
    for channel in channels:
        obj = get_bone(rig, hierarchy, channel)

        if channel.delta_type == 0:
            apply_motion_channel_time_coded(obj, channel)
        else:
            apply_adaptive_delta(obj, channel)


def create_animation(rig, animation, hierarchy, compressed=False):
    if animation is None:
        return

    if rig is None and animation.header.hierarchy_name in bpy.data.objects:
        obj = bpy.data.objects[animation.header.hierarchy_name]
        if obj.type == 'ARMATURE':
            rig = obj

    setup_animation(animation)

    if not compressed:
        process_channels(hierarchy, animation.channels,
                         rig, apply_uncompressed)
    else:
        process_channels(hierarchy, animation.time_coded_channels,
                         rig, apply_timecoded)
        process_channels(hierarchy, animation.adaptive_delta_channels,
                         rig, apply_adaptive_delta)
        process_motion_channels(hierarchy, animation.motion_channels, rig)

    bpy.context.scene.frame_set(0)


##########################################################################
# create basic meshes
##########################################################################


def create_sphere():
    mesh = bpy.data.meshes.new('Basic_Sphere')
    basic_sphere = bpy.data.objects.new("Basic_Sphere", mesh)

    b_mesh = bmesh.new()
    bmesh.ops.create_uvsphere(b_mesh, u_segments=12, v_segments=6, diameter=35)
    b_mesh.to_mesh(mesh)
    b_mesh.free()

    return basic_sphere


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
    box_object.display_type = 'WIRE'
    mat = bpy.data.materials.new(box.name() + ".Material")

    mat.diffuse_color = box.color.to_vector_rgba()
    cube.materials.append(mat)
    box_object.location = box.center
    link_object_to_active_scene(box_object, coll)

    if hierarchy is None or rig is None:
        return

    sub_objects = [
        sub_object for sub_object in hlod.lod_array.sub_objects if sub_object.name() == box.name()]
    if not sub_objects:
        return
    sub_object = sub_objects[0]
    if sub_object.bone_index == 0:
        return
    pivot = hierarchy.pivots[sub_object.bone_index]
    box_object.parent = rig
    box_object.parent_bone = pivot.name
    box_object.parent_type = 'BONE'
