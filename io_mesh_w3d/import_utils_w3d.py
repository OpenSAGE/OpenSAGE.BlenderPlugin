# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import os
import bpy
import bmesh
import sys

from mathutils import Vector, Matrix, Quaternion

from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.image_utils import load_image

from io_mesh_w3d.io_binary import read_chunk_head
from io_mesh_w3d.w3d_adaptive_delta import decode

from io_mesh_w3d.structs.w3d_vertex_material import *


def read_chunk_array(self, io_stream, chunk_end, type_, read_func):
    result = []

    while io_stream.tell() < chunk_end:
        (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

        if chunk_type == type_:
            result.append(read_func(self, io_stream, subchunk_end))
        else:
            skip_unknown_chunk(self, io_stream, chunk_type, chunk_size)
    return result


def insensitive_path(path):
     # find the io_stream on unix
    directory = os.path.dirname(path)
    name = os.path.basename(path)

    for io_streamname in os.listdir(directory):
        if io_streamname.lower() == name.lower():
            path = os.path.join(directory, io_streamname)
    return path


def skip_unknown_chunk(self, io_stream, chunk_type, chunk_size):
    message = "WARNING: unknown chunk_type in io_stream: %s" % hex(chunk_type)
    print(message)
    if self is not None:
        self.report({'ERROR'}, message)
    io_stream.seek(chunk_size, 1)


def link_object_to_active_scene(obj, coll, appendix=""):
    if obj.name in coll.objects:
        obj.name += appendix
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


#######################################################################################
# mesh
#######################################################################################


def create_mesh(self, mesh_struct, hierarchy, rig):
    triangles = []

    for triangle in mesh_struct.triangles:
        triangles.append(triangle.vert_ids)

    mesh = bpy.data.meshes.new(mesh_struct.header.mesh_name)

    verts = mesh_struct.verts.copy()
    if rig is not None:
        for i, vert_inf in enumerate(mesh_struct.vert_infs):
            weight = vert_inf.bone_inf
            if weight == 0.0:
                weight = 1.0

            bone = rig.data.bones[hierarchy.pivots[vert_inf.bone_idx].name]
            verts[i] = bone.matrix_local @ mesh_struct.verts[i]

    mesh.from_pydata(verts, [], triangles)
    mesh.update()
    mesh.validate()

    smooth_mesh(mesh)

    mesh_ob = bpy.data.objects.new(mesh_struct.header.mesh_name, mesh)
    mesh_ob['UserText'] = mesh_struct.user_text

    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    for mat_pass in mesh_struct.material_passes:
        create_uvlayers(mesh, b_mesh, triangles, mat_pass)

    for shaderMat in mesh_struct.shader_materials:
        mesh.materials.append(create_material_from_shader_material(
            self, mesh_struct, shaderMat))

    for vertMat in mesh_struct.vert_materials:
        mesh.materials.append(
            create_material_from_vertex_material(self, mesh_struct, vertMat))

    for i, texture in enumerate(mesh_struct.textures):
        create_principled_bsdf(
            self, material=mesh.materials[i], diffuse_tex=texture.name)

    for i, shader in enumerate(mesh_struct.shaders):
        set_shader_properties(mesh.materials[i], shader)


def rig_mesh(mesh_struct, hierarchy, rig, coll):
    mesh_ob = bpy.data.objects[mesh_struct.header.mesh_name]
    link_object_to_active_scene(mesh_ob, coll)

    if hierarchy is None or not hierarchy.pivots:
        return

    if mesh_struct.is_skin():
        for pivot in hierarchy.pivots:
            mesh_ob.vertex_groups.new(name=pivot.name)

        for i in range(len(mesh_struct.vert_infs)):
            weight = mesh_struct.vert_infs[i].bone_inf
            if weight < 0.01:
                weight = 1.0

            mesh_ob.vertex_groups[mesh_struct.vert_infs[i].bone_idx].add(
                [i], weight, 'REPLACE')

            if mesh_struct.vert_infs[i].xtra_idx != 0:
                mesh_ob.vertex_groups[mesh_struct.vert_infs[i].xtra_idx].add(
                    [i], mesh_struct.vert_infs[i].xtra_inf, 'ADD')

        mod = mesh_ob.modifiers.new(rig.name, 'ARMATURE')
        mod.object = rig
        mod.use_bone_envelopes = False
        mod.use_vertex_groups = True

    else:
        pivot = [pivot for pivot in hierarchy.pivots if pivot.name ==
                 mesh_struct.header.mesh_name][0]
        if pivot is None:
            return

        mesh_ob.rotation_mode = 'QUATERNION'
        mesh_ob.location = pivot.translation
        mesh_ob.rotation_euler = pivot.euler_angles
        mesh_ob.rotation_quaternion = pivot.rotation

        if pivot.parent_id == 0:
            return

        parent_pivot = hierarchy.pivots[pivot.parent_id]

        if parent_pivot.name in bpy.data.objects:
            mesh_ob.parent = bpy.data.objects[parent_pivot.name]
        else:
            mesh_ob.parent = rig
            mesh_ob.parent_bone = parent_pivot.name
            mesh_ob.parent_type = 'BONE'


#######################################################################################
# skeleton
#######################################################################################


def get_or_create_skeleton(hlod, hierarchy, coll):
    rig = None

    if hlod is None or hierarchy is None:
        return rig

    if hlod.header.model_name == hlod.header.hierarchy_name:
        amtName = hierarchy.header.name + "SKL"
    else:
        amtName = hierarchy.header.name

    for obj in bpy.data.objects:
        if obj.name == amtName:
            rig = obj

    if rig is None:
        rig = create_armature(hierarchy, amtName,
                              hlod.lod_array.sub_objects, coll)
    return rig


def make_transform_matrix(loc, rot):
    mat_loc = Matrix.Translation(loc)
    mat_rot = Quaternion(rot).to_matrix().to_4x4()
    return mat_loc @ mat_rot


def create_armature(hierarchy, amt_name, sub_objects, coll):
    amt = bpy.data.armatures.new(hierarchy.header.name)
    amt.show_names = False

    root = hierarchy.pivots[0]

    rig = bpy.data.objects.new(amt_name, amt)
    rig.location = root.translation
    rig.rotation_mode = 'QUATERNION'
    rig.track_axis = "POS_X"

    link_object_to_active_scene(rig, coll, "SKL")
    bpy.ops.object.mode_set(mode='EDIT')

    non_bone_pivots = []
    basic_sphere = create_sphere()

    for obj in sub_objects:
        non_bone_pivots.append(hierarchy.pivots[obj.bone_index])

    for pivot in hierarchy.pivots:
        if pivot.parent_id == -1 or non_bone_pivots.count(pivot) > 0:
            continue

        bone = amt.edit_bones.new(pivot.name)
        matrix = make_transform_matrix(pivot.translation, pivot.rotation)

        if pivot.parent_id > 0:
            parent_pivot = hierarchy.pivots[pivot.parent_id]
            bone.parent = amt.edit_bones[parent_pivot.name]
            matrix = bone.parent.matrix @ matrix

        bone.head = Vector((0.0, 0.0, 0.0))
        # has to point in y direction, so that the rotation is applied correctly
        bone.tail = Vector((0.0, 0.01, 0.0))
        bone.matrix = matrix

    bpy.ops.object.mode_set(mode='POSE')

    for bone in rig.pose.bones:
        bone.custom_shape = basic_sphere

    bpy.ops.object.mode_set(mode='OBJECT')

    return rig


#######################################################################################
# create material
#######################################################################################


def rgba_to_vector(rgba, scale=255.0):
    return (rgba.r / scale, rgba.g / scale, rgba.b / scale, 0.0)


def create_material_from_vertex_material(self, mesh, vert_mat):
    mat = bpy.data.materials.new(
        mesh.header.mesh_name + "." + vert_mat.vm_name)
    mat.use_nodes = True
    #mat.blend_method = 'BLEND'

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

    mat.attributes = atts
    mat.specular_intensity = vert_mat.vm_info.shininess
    mat.specular_color = rgba_to_vector(vert_mat.vm_info.specular)[0:3]
    mat.diffuse_color = rgba_to_vector(vert_mat.vm_info.diffuse)

    mat.emission = rgba_to_vector(vert_mat.vm_info.emissive)
    mat.ambient = rgba_to_vector(vert_mat.vm_info.ambient)
    mat.translucency = vert_mat.vm_info.translucency
    mat.opacity = vert_mat.vm_info.opacity

    mat.vm_args_0 = vert_mat.vm_args_0
    mat.vm_args_1 = vert_mat.vm_args_1

    create_principled_bsdf(self, material=mat,
                           base_color=rgba_to_vector(vert_mat.vm_info.diffuse)[0:3], alpha=vert_mat.vm_info.opacity)
    return mat


def create_material_from_shader_material(self, mesh, shader_mat):
    material = bpy.data.materials.new(
        mesh.header.mesh_name + ".ShaderMaterial")
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
            material.ambient = rgba_to_vector(prop.value)
        elif prop.name == "DiffuseColor":
            material.diffuse_color = rgba_to_vector(prop.value)
        elif prop.name == "SpecularColor":
            material.specular_color = rgba_to_vector(prop.value)[0:3]
        elif prop.name == "AlphaTestEnable":
            material.alpha_test = bool(prop.value)
        elif prop.name == "BlendMode":
            material.blend_mode = prop.value
        elif prop.name == "BumpUVScale":
            material.bump_uv_scale = prop.value
        elif prop.name == "Sampler_ClampU_ClampV_NoMip_0":
            material.sampler_clamp_uv_no_mip = prop.value
        else:
            print("!!! shader property not implemented: " + prop.name)
            self.report(
                {'ERROR'}, "shader property not implemented: " + prop.name)

    create_principled_bsdf(self, material=material, diffuse_tex=diffuse,
                           normal_tex=normal, bump_scale=bump_scale)
    return material


def create_principled_bsdf(self, material, base_color=None, alpha=0, diffuse_tex=None, normal_tex=None, bump_scale=0):
    principled = PrincipledBSDFWrapper(material, is_readonly=False)
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


#######################################################################################
# set shader properties
#######################################################################################


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


#######################################################################################
# create uvlayer
#######################################################################################


def create_uv_layer(mesh, b_mesh, tris, tx_coords, index=""):
    if not tx_coords:
        return

    uv_layer = mesh.uv_layers.new(name="texcoords" + index, do_init=False)
    for i, face in enumerate(b_mesh.faces):
        tri = tris[i]
        for loop in face.loops:
            idx = tri[loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx]


def create_uvlayers(mesh, b_mesh, tris, mat_pass):
    create_uv_layer(mesh, b_mesh, tris, mat_pass.tx_coords)

    if len(mat_pass.tx_stages) > 1:
        print("Warning!: only one texture stage per material pass supported on export")

    for i, stage in enumerate(mat_pass.tx_stages):
        create_uv_layer(mesh, b_mesh, tris, stage.tx_coords, str(i))


#######################################################################################
# load texture
#######################################################################################

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


#######################################################################################
# createAnimation
#######################################################################################


def is_roottransform(pivot):
    return pivot == 0


def is_translation(channel):
    return channel.type == 0 or channel.type == 1 or channel.type == 2


def is_rotation(channel):
    return channel.type == 6


def get_bone(rig, name):
    # sometimes objects are animated, not just bones
    if rig is not None and name in rig.pose.bones:
        return rig.pose.bones[name]
    return bpy.data.objects[name]


def setup_animation(animation):
    bpy.data.scenes["Scene"].render.fps = animation.header.frame_rate
    bpy.data.scenes["Scene"].frame_start = 0
    bpy.data.scenes["Scene"].frame_end = animation.header.num_frames - 1


def set_translation(bone, index, frame, value):
    bone.location[index] = value
    # TODO: how to use option flag: INSERTKEY_NEEDED
    bone.keyframe_insert(data_path='location', index=index, frame=frame)


def set_rotation(bone, frame, value):
    bone.rotation_mode = 'QUATERNION'
    bone.rotation_quaternion = value
    # TODO: how to use option flag: INSERTKEY_NEEDED
    bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)


def set_transform(bone, channel, frame, value):
    if is_translation(channel):
        set_translation(bone, channel.type, frame, value)
    elif is_rotation(channel):
        set_rotation(bone, frame, value)


def apply_timecoded(bone, channel):
    for key in channel.time_codes:
        set_transform(bone, channel, key.time_code, key.value)


def apply_motion_channel_time_coded(bone, channel):
    for dat in channel.data:
        set_transform(bone, channel, dat.time_code, dat.value)


def apply_adaptive_delta(bone, channel):
    data = decode(channel)
    for i in range(channel.num_time_codes):
        set_transform(bone, channel, i, data[i])


def apply_uncompressed(bone, channel):
    for frame in range(channel.first_frame, channel.last_frame):
        data = channel.data[frame - channel.first_frame]
        set_transform(bone, channel, frame, data)


def process_channels(hierarchy, channels, rig, apply_func):
    for channel in channels:
        if is_roottransform(channel.pivot):
            continue

        pivot = hierarchy.pivots[channel.pivot]
        obj = get_bone(rig, pivot.name)

        apply_func(obj, channel)


def process_motion_channels(hierarchy, channels, rig):
    for channel in channels:
        if is_roottransform(channel.pivot):
            continue

        pivot = hierarchy.pivots[channel.pivot]
        obj = get_bone(rig, pivot.name)

        if channel.delta_type == 0:
            apply_motion_channel_time_coded(obj, channel)
        else:
            apply_adaptive_delta(obj, channel)


def create_animation(rig, animation, hierarchy, compressed=False):
    if animation is None:
        return

    if rig is None:
        rig = bpy.data.objects[animation.header.hierarchy_name]

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


#######################################################################################
# create basic meshes
#######################################################################################


def create_sphere():
    mesh = bpy.data.meshes.new('Basic_Sphere')
    basic_sphere = bpy.data.objects.new("Basic_Sphere", mesh)

    b_mesh = bmesh.new()
    bmesh.ops.create_uvsphere(b_mesh, u_segments=12, v_segments=6, diameter=35)
    b_mesh.to_mesh(mesh)
    b_mesh.free()

    return basic_sphere


def create_box(box, coll):
    if box is None:
        return

    # to keep name always equal (sometimes it is "BOUNDING BOX")
    name = "BOUNDINGBOX"
    x = box.extend[0]/2.0
    y = box.extend[1]/2.0
    z = box.extend[2]

    verts = [(x, y, z), (-x, y, z), (-x, -y, z), (x, -y, z),
             (x, y, 0), (-x, y, 0), (-x, -y, 0), (x, -y, 0)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]

    cube = bpy.data.meshes.new(name)
    box_object = bpy.data.objects.new(name, cube)
    box_object.display_type = 'WIRE'
    mat = bpy.data.materials.new("BOUNDINGBOX.Material")

    mat.diffuse_color = rgba_to_vector(box.color)
    cube.materials.append(mat)
    box_object.location = box.center
    link_object_to_active_scene(box_object, coll)
    cube.from_pydata(verts, [], faces)
    cube.update(calc_edges=True)
