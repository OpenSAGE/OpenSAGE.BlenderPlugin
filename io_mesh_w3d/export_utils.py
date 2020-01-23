# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os

import bmesh
import bpy
from bpy_extras import node_shader_utils

from io_mesh_w3d.shared.structs.animation import *
from io_mesh_w3d.shared.structs.collision_box import *
from io_mesh_w3d.shared.structs.hierarchy import *
from io_mesh_w3d.shared.structs.hlod import *
from io_mesh_w3d.shared.structs.mesh import *
from io_mesh_w3d.w3d.structs.dazzle import *
from io_mesh_w3d.w3d.structs.compressed_animation import *
from io_mesh_w3d.w3d.structs.mesh_structs.shader import *

pick_plane_names = ['PICK']


def get_objects(type, object_list=None):  # MESH, ARMATURE
    if object_list is None:
        object_list = bpy.context.scene.objects
    return [object for object in object_list if object.type == type]


def switch_to_pose(rig, pose):
    if rig is not None:
        rig.data.pose_position = pose
        bpy.context.view_layer.update()


##########################################################################
# Mesh data
##########################################################################


def retrieve_boxes(hierarchy, container_name):
    boxes = []

    for mesh_object in get_objects('MESH'):
        if mesh_object.object_type != 'BOX':
            continue
        name = container_name + '.' + mesh_object.name
        box = CollisionBox(
            name_=name,
            center=mesh_object.location)
        box_mesh = mesh_object.to_mesh(
            preserve_all_data_layers=False, depsgraph=None)
        box.extend = Vector(
            (box_mesh.vertices[0].co.x * 2,
             box_mesh.vertices[0].co.y * 2,
             box_mesh.vertices[0].co.z))

        for material in box_mesh.materials:
            box.color = RGBA(material.diffuse_color)
        boxes.append(box)
    return boxes


def retrieve_dazzles(hierarchy, container_name):
    dazzles = []

    for mesh_object in get_objects('MESH'):
        if mesh_object.object_type != 'DAZZLE':
            continue
        name = container_name + '.' + mesh_object.name
        dazzle = Dazzle(
            name_=name,
            type_name=mesh_object.dazzle_type)

        dazzles.append(dazzle)
    return dazzles


def retrieve_meshes(context, hierarchy, rig, container_name):
    mesh_structs = []

    switch_to_pose(rig, 'REST')

    for mesh_object in get_objects('MESH'):
        if mesh_object.object_type != 'NORMAL':
            continue

        if mesh_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh_struct = Mesh(
            header=MeshHeader(
                attrs=GEOMETRY_TYPE_NORMAL),
            vert_channel_flags=VERTEX_CHANNEL_LOCATION | VERTEX_CHANNEL_NORMAL,
            face_channel_flags=1,
            user_text='',
            verts=[],
            normals=[],
            tangents=[],
            bitangents=[],
            vert_infs=[],
            triangles=[],
            shade_ids=[],
            shaders=[],
            vert_materials=[],
            textures=[],
            material_passes=[],
            shader_materials=[],
            multi_bone_skinned=False)

        header = mesh_struct.header
        header.mesh_name = mesh_object.name
        header.container_name = container_name

        mesh_struct.user_text = mesh_object.userText

        if mesh_object.hide_get():
            header.attrs |= GEOMETRY_TYPE_HIDDEN

        mesh = mesh_object.to_mesh(
            preserve_all_data_layers=False, depsgraph=None)

        triangulate(mesh)
        header.vert_count = len(mesh.vertices)

        (center, radius) = calculate_mesh_sphere(mesh)
        header.sph_center = center
        header.sph_radius = radius

        for i, vertex in enumerate(mesh.vertices):
            if vertex.groups:
                vertInf = VertexInfluence()
                for index, pivot in enumerate(hierarchy.pivots):
                    if pivot.name == mesh_object.vertex_groups[vertex.groups[0].group].name:
                        vertInf.bone_idx = index
                vertInf.bone_inf = vertex.groups[0].weight
                mesh_struct.vert_infs.append(vertInf)

                matrix = None
                if vertInf.bone_idx > 0:
                    matrix = rig.pose.bones[hierarchy.pivots[vertInf.bone_idx].name].matrix
                else:
                    matrix = rig.matrix_local

                mesh_struct.verts.append(
                    matrix.inverted() @ vertex.co.xyz)

                if len(vertex.groups) > 1:
                    mesh_struct.multi_bone_skinned = True
                    for index, pivot in enumerate(hierarchy.pivots):
                        if pivot.name == mesh_object.vertex_groups[vertex.groups[1].group].name:
                            vertInf.xtra_idx = index
                    vertInf.xtra_inf = vertex.groups[1].weight

                if len(vertex.groups) > 2:
                    context.warning('max 2 bone influences per vertex supported!')

            else:
                mesh_struct.verts.append(vertex.co.xyz)

            mesh_struct.normals.append(vertex.normal)
            mesh_struct.shade_ids.append(i)

        header.min_corner = Vector(
            (mesh_object.bound_box[0][0],
             mesh_object.bound_box[0][1],
             mesh_object.bound_box[0][2]))
        header.max_corner = Vector(
            (mesh_object.bound_box[6][0],
             mesh_object.bound_box[6][1],
             mesh_object.bound_box[6][2]))

        if mesh.uv_layers:
            mesh.calc_tangents()
            mesh_struct.header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT | VERTEX_CHANNEL_BITANGENT
            mesh_struct.tangents = [Vector] * len(mesh_struct.normals)
            mesh_struct.bitangents = [Vector] * len(mesh_struct.normals)

        for face in mesh.polygons:
            triangle = Triangle()
            triangle.vert_ids = list(face.vertices)
            triangle.normal = Vector(face.normal)
            vec1 = mesh.vertices[face.vertices[0]].normal
            vec2 = mesh.vertices[face.vertices[1]].normal
            vec3 = mesh.vertices[face.vertices[2]].normal
            tri_pos = (vec1 + vec2 + vec3) / 3.0
            triangle.distance = tri_pos.length
            mesh_struct.triangles.append(triangle)

            if mesh.uv_layers:
                for vert in [mesh.loops[i] for i in face.loop_indices]:
                    # TODO: compute the mean value from the
                    # face-vertex-tangents etc?
                    normal = vert.normal
                    tangent = vert.tangent
                    mesh_struct.tangents[vert.vertex_index] = tangent
                    bitangent = vert.bitangent_sign * normal.cross(tangent)
                    mesh_struct.bitangents[vert.vertex_index] = bitangent

        header.face_count = len(mesh_struct.triangles)

        if mesh_struct.vert_infs:
            header.attrs |= GEOMETRY_TYPE_SKIN

        center, radius = calculate_mesh_sphere(mesh)
        header.sphCenter = center
        header.sphRadius = radius

        b_mesh = bmesh.new()
        b_mesh.from_mesh(mesh)

        tx_stages = []
        multiple_uvs_per_vertex = False
        for i, uv_layer in enumerate(mesh.uv_layers):
            stage = TextureStage(
                tx_ids=[i],
                per_face_tx_coords=[],
                tx_coords=[None] * len(mesh_struct.verts))

            for j, face in enumerate(b_mesh.faces):
                for loop in face.loops:
                    vert_index = mesh_struct.triangles[j].vert_ids[loop.index % 3]
                    if stage.tx_coords[vert_index] is not None \
                            and stage.tx_coords[vert_index] != uv_layer.data[loop.index].uv:
                        multiple_uvs_per_vertex = True
                    stage.tx_coords[vert_index] = uv_layer.data[loop.index].uv
            tx_stages.append(stage)

        if multiple_uvs_per_vertex:
            context.warning('w3d file format does not support multiple uv coords per vertex, try another unwrapping method')

        for i, material in enumerate(mesh.materials):
            mat_pass = MaterialPass(
                vertex_material_ids=[],
                shader_ids=[],
                dcg=[],
                dig=[],
                scg=[],
                shader_material_ids=[],
                tx_stages=[],
                tx_coords=[])

            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)

            if principled.normalmap_texture is not None:  # TODO: or W3X export
                mat_pass.shader_material_ids = [i]
                if i < len(tx_stages):
                    mat_pass.tx_coords = tx_stages[i].tx_coords
                mesh_struct.shader_materials.append(
                    retrieve_shader_material(material, principled))
            else:
                mesh_struct.shaders.append(retrieve_shader(material))
                mat_pass.shader_ids = [i]
                mat_pass.vertex_material_ids = [i]
                if i < len(tx_stages):
                    mat_pass.tx_stages.append(tx_stages[i])
                mesh_struct.vert_materials.append(
                    retrieve_vertex_material(material))

                if principled.base_color_texture.image is not None:
                    info = TextureInfo(
                        attributes=0,
                        animation_type=0,
                        frame_count=0,
                        frame_rate=0.0)
                    img = principled.base_color_texture.image
                    filepath = os.path.basename(img.filepath)
                    if filepath == '':
                        filepath = img.name + '.dds'
                    tex = Texture(
                        id=img.name,
                        file=filepath,
                        texture_info=info)
                    mesh_struct.textures.append(tex)

            mesh_struct.material_passes.append(mat_pass)

        header.vert_channel_flags = VERTEX_CHANNEL_LOCATION | VERTEX_CHANNEL_NORMAL

        if mesh_struct.shader_materials and mesh.uv_layers:
            header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT | VERTEX_CHANNEL_BITANGENT
        else:
            mesh_struct.tangents = []
            mesh_struct.bitangents = []

        mesh_struct.mat_info = MaterialInfo(
            pass_count=len(mesh_struct.material_passes),
            vert_matl_count=len(mesh_struct.vert_materials),
            shader_count=len(mesh_struct.shaders),
            texture_count=len(mesh_struct.textures))

        mesh_struct.header.matl_count = max(
            len(mesh_struct.vert_materials), len(mesh_struct.shader_materials))
        mesh_structs.append(mesh_struct)

    switch_to_pose(rig, 'POSE')

    return mesh_structs


##########################################################################
# hlod
##########################################################################

# hardcoded for now, provide export options?
screen_sizes = [MAX_SCREEN_SIZE, 1.0, 0.3, 0.03]


def create_lod_array(meshes, hierarchy, container_name, lod_arrays):
    if not meshes:
        return lod_arrays

    index = min(len(lod_arrays), len(screen_sizes) - 1)

    lod_array = HLodLodArray(
        header=HLodArrayHeader(
            model_count=len(meshes),
            max_screen_size=screen_sizes[index]),
        sub_objects=[])

    for mesh in meshes:
        subObject = HLodSubObject(
            name=mesh.name,
            identifier=container_name + '.' + mesh.name,
            bone_index=0,
            is_box=mesh.object_type == 'BOX')

        if not mesh.vertex_groups:
            for index, pivot in enumerate(hierarchy.pivots):
                if pivot.name == mesh.name or pivot.name == mesh.parent_bone:
                    subObject.bone_index = index

        lod_array.sub_objects.append(subObject)

    lod_arrays.append(lod_array)
    return lod_arrays


def create_hlod(hierarchy, container_name):
    hlod = HLod(
        header=HLodHeader(
            model_name=container_name,
            hierarchy_name=hierarchy.name()),
        lod_arrays=[])

    meshes = get_objects('MESH', bpy.context.scene.collection.objects)
    lod_arrays = create_lod_array(meshes, hierarchy, container_name, [])

    for coll in bpy.data.collections:
        meshes = get_objects('MESH', coll.objects)
        lod_arrays = create_lod_array(
            meshes, hierarchy, container_name, lod_arrays)

    for lod_array in reversed(lod_arrays):
        hlod.lod_arrays.append(lod_array)
    hlod.header.lod_count = len(hlod.lod_arrays)
    return hlod


##########################################################################
# material data
##########################################################################


def retrieve_vertex_material(material):
    info = VertexMaterialInfo(
        attributes=0,
        shininess=material.specular_intensity,
        specular=RGBA(vec=material.specular_color, a=0),
        diffuse=RGBA(vec=material.diffuse_color, a=0),
        emissive=RGBA(vec=material.emission),
        ambient=RGBA(vec=material.ambient),
        translucency=material.translucency,
        opacity=material.opacity)

    if 'USE_DEPTH_CUE' in material.attributes:
        info.attributes |= USE_DEPTH_CUE
    if 'ARGB_EMISSIVE_ONLY' in material.attributes:
        info.attributes |= ARGB_EMISSIVE_ONLY
    if 'COPY_SPECULAR_TO_DIFFUSE' in material.attributes:
        info.attributes |= COPY_SPECULAR_TO_DIFFUSE
    if 'DEPTH_CUE_TO_ALPHA' in material.attributes:
        info.attributes |= DEPTH_CUE_TO_ALPHA

    vert_material = VertexMaterial(
        vm_name=material.name.split('.', 1)[-1],
        vm_info=info,
        vm_args_0=material.vm_args_0,
        vm_args_1=material.vm_args_1)

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
    elif type == 4 and default is None:
        default = Vector()
    elif type == 5 and default is None:
        default = RGBA(r=255, g=255, b=255)
    elif type == 6 and default is None:
        default = 0
    elif type == 7 and default is None:
        default = False

    if value == default:
        return
    shader_mat.properties.append(ShaderMaterialProperty(
        type=type, name=name, value=value))


def retrieve_shader_material(material, principled, w3x=False):
    shader_mat = ShaderMaterial(
        header=ShaderMaterialHeader(
            type_name='NormalMapped.fx'),
        properties=[])

    shader_mat.header.technique_index = material.technique

    if w3x:
        append_property(shader_mat, 2, 'Shininess', material.specular_intensity, 0.5)
        append_property(shader_mat, 5, 'ColorDiffuse', RGBA(material.diffuse_color),
                        RGBA(r=204, g=204, b=204, a=255))
        append_property(shader_mat, 5, 'ColorSpecular', RGBA(material.specular_color, a=0.0))
        append_property(shader_mat, 5, 'ColorAmbient', RGBA(material.ambient))
        append_property(shader_mat, 5, 'ColorEmissive', RGBA(material.emission))

    else:
        append_property(shader_mat, 2, 'SpecularExponent', material.specular_intensity, 0.5)
        append_property(shader_mat, 5, 'DiffuseColor', RGBA(material.diffuse_color),
                        RGBA(r=204, g=204, b=204, a=255))
        append_property(shader_mat, 5, 'SpecularColor', RGBA(material.specular_color, a=0.0))
        append_property(shader_mat, 5, 'AmbientColor', RGBA(material.ambient))
        append_property(shader_mat, 5, 'EmissiveColor', RGBA(material.emission))

    append_property(shader_mat, 1, 'DiffuseTexture', principled.base_color_texture)
    append_property(shader_mat, 1, 'NormalMap', principled.normalmap_texture)
    if principled.normalmap_texture is not None:
        append_property(shader_mat, 2, 'BumpScale', principled.normalmap_strength, 1.0)
    append_property(shader_mat, 1, 'SpecMap', principled.specular_texture)
    append_property(shader_mat, 7, 'CullingEnable', material.use_backface_culling)
    append_property(shader_mat, 2, 'Opacity', material.opacity)
    append_property(shader_mat, 7, 'AlphaTestEnable', material.alpha_test)
    append_property(shader_mat, 6, 'BlendMode', material.blend_mode)
    append_property(shader_mat, 3, 'BumpUVScale', material.bump_uv_scale)
    append_property(shader_mat, 6, 'EdgeFadeOut', material.edge_fade_out)
    append_property(shader_mat, 7, 'DepthWriteEnable', material.depth_write)
    append_property(shader_mat, 4, 'Sampler_ClampU_ClampV_NoMip_0',
                    material.sampler_clamp_uv_no_mip_0)
    append_property(shader_mat, 4, 'Sampler_ClampU_ClampV_NoMip_1',
                    material.sampler_clamp_uv_no_mip_1)

    append_property(shader_mat, 6, 'NumTextures', material.num_textures)
    append_property(shader_mat, 1, 'Texture_0', material.texture_0)
    append_property(shader_mat, 1, 'Texture_1', material.texture_1)

    append_property(shader_mat, 6, 'SecondaryTextureBlendMode',
                    material.secondary_texture_blend_mode)
    append_property(shader_mat, 6, 'TexCoordMapper_0',
                    material.tex_coord_mapper_0)
    append_property(shader_mat, 6, 'TexCoordMapper_1',
                    material.tex_coord_mapper_1)
    append_property(shader_mat, 5, 'TexCoordTransform_0',
                    RGBA(material.tex_coord_transform_0), RGBA())
    append_property(shader_mat, 5, 'TexCoordTransform_1',
                    RGBA(material.tex_coord_transform_1), RGBA())
    append_property(shader_mat, 1, 'EnvironmentTexture',
                    material.environment_texture)
    append_property(shader_mat, 2, 'EnvMult',
                    material.environment_mult)
    append_property(shader_mat, 1, 'RecolorTexture',
                    material.recolor_texture)
    append_property(shader_mat, 2, 'RecolorMultiplier',
                    material.recolor_mult)
    append_property(shader_mat, 7, 'UseRecolorColors',
                    material.use_recolor)
    append_property(shader_mat, 7, 'HouseColorPulse',
                    material.house_color_pulse)
    append_property(shader_mat, 1, 'ScrollingMaskTexture',
                    material.scrolling_mask_texture)
    append_property(shader_mat, 2, 'TexCoordTransformAngle_0',
                    material.tex_coord_transform_angle)
    append_property(shader_mat, 2, 'TexCoordTransformU_0',
                    material.tex_coord_transform_u_0)
    append_property(shader_mat, 2, 'TexCoordTransformV_0',
                    material.tex_coord_transform_v_0)
    append_property(shader_mat, 2, 'TexCoordTransformU_1',
                    material.tex_coord_transform_u_1)
    append_property(shader_mat, 2, 'TexCoordTransformV_1',
                    material.tex_coord_transform_v_1)
    append_property(shader_mat, 2, 'TexCoordTransformU_2',
                    material.tex_coord_transform_u_2)
    append_property(shader_mat, 2, 'TexCoordTransformV_2',
                    material.tex_coord_transform_v_2)
    append_property(shader_mat, 5, 'TextureAnimation_FPS_NumPerRow_LastFrame_FrameOffset_0',
                    RGBA(material.tex_ani_fps_NPR_lastFrame_frameOffset_0), RGBA())

    return shader_mat


##########################################################################
# shader data
##########################################################################


def retrieve_shader(material):
    return Shader(
        depth_compare=material.shader.depth_compare,
        depth_mask=material.shader.depth_mask,
        color_mask=material.shader.color_mask,
        dest_blend=material.shader.dest_blend,
        fog_func=material.shader.fog_func,
        pri_gradient=material.shader.pri_gradient,
        sec_gradient=material.shader.sec_gradient,
        src_blend=material.shader.src_blend,
        texturing=material.shader.texturing,
        detail_color_func=material.shader.detail_color_func,
        detail_alpha_func=material.shader.detail_alpha_func,
        shader_preset=material.shader.shader_preset,
        alpha_test=material.shader.alpha_test,
        post_detail_color_func=material.shader.post_detail_color_func,
        post_detail_alpha_func=material.shader.post_detail_alpha_func)


##########################################################################
# hierarchy data
##########################################################################

def process_pivot(pivot, pivots, hierarchy, processed):
    processed.append(pivot.name)
    hierarchy.pivots.append(pivot)
    children = [child for child in pivots if child.parent_id == pivot.name]
    parent_index = len(hierarchy.pivots) - 1
    for child in children:
        child.parent_id = parent_index
        process_pivot(child, pivots, hierarchy, processed)
    return processed


def retrieve_hierarchy(context, container_name):
    hierarchy = Hierarchy(
        header=HierarchyHeader(),
        pivots=[],
        pivot_fixups=[])

    root = HierarchyPivot(
        name='ROOTTRANSFORM',
        parentID=-1,
        translation=Vector())
    hierarchy.pivots.append(root)

    rig = None
    rigs = get_objects('ARMATURE')
    pivots = []

    if len(rigs) == 0:
        hierarchy.header.name = container_name
        hierarchy.header.center_pos = Vector()
    elif len(rigs) == 1:
        rig = rigs[0]

        switch_to_pose(rig, 'REST')

        root.translation = rig.location

        hierarchy.header.name = rig.name
        hierarchy.header.center_pos = rig.location

        for bone in rig.pose.bones:
            pivot = HierarchyPivot(
                name=bone.name,
                parent_id=0)

            matrix = bone.matrix

            if bone.parent is not None:
                pivot.parent_id = bone.parent.name
                matrix = bone.parent.matrix.inverted() @ matrix

            (translation, rotation, _) = matrix.decompose()
            pivot.translation = translation
            pivot.rotation = rotation
            eulers = rotation.to_euler()
            pivot.euler_angles = Vector((eulers.x, eulers.y, eulers.z))

            pivots.append(pivot)

        switch_to_pose(rig, 'POSE')
    else:
        context.error('only one armature per scene allowed!')
        return (None, None)

    meshes = []
    if rig is not None:
        for coll in bpy.data.collections:
            if rig.name in coll.objects:
                meshes = get_objects('MESH', coll.objects)
    else:
        meshes = get_objects('MESH')

    for mesh in meshes:
        if mesh.vertex_groups \
                or mesh.object_type == 'BOX' \
                or mesh.name in pick_plane_names:
            continue

        if mesh.delta_location.length < 0.01 \
                and mesh.delta_rotation_quaternion == Quaternion():
            continue

        eulers = mesh.rotation_quaternion.to_euler()
        pivot = HierarchyPivot(
            name=mesh.name,
            parent_id=0,
            translation=mesh.delta_location,
            rotation=mesh.delta_rotation_quaternion,
            euler_angles=Vector((eulers.x, eulers.y, eulers.z)))

        if mesh.parent_bone != '':
            pivot.parent_id = mesh.parent_bone
        elif mesh.parent is not None:
            pivot.parent_id = mesh.parent.name

        pivots.append(pivot)

    processed = []
    for pivot in pivots:
        if pivot.name in processed:
            continue
        processed = process_pivot(pivot, pivots, hierarchy, processed)

    hierarchy.header.num_pivots = len(hierarchy.pivots)

    return (hierarchy, rig)


##########################################################################
# Animation data
##########################################################################


def is_rotation(fcu):
    return 'rotation_quaternion' in fcu.data_path


def is_visibility(fcu):
    return 'hide' in fcu.data_path


def retrieve_channels(obj, hierarchy, timecoded, name=None):
    if obj.animation_data is None or obj.animation_data.action is None:
        return []

    channel = None
    channels = []

    for fcu in obj.animation_data.action.fcurves:
        if name is None:
            values = fcu.data_path.split('"')
            if len(values) == 1:
                pivot_name = 'ROOTTRANSFORM'
            else:
                pivot_name = values[1]
        else:
            pivot_name = name

        pivot_index = 0
        for i, pivot in enumerate(hierarchy.pivots):
            if pivot.name == pivot_name:
                pivot_index = i

        channel_type = fcu.array_index
        vec_len = 1

        if is_rotation(fcu):
            channel_type = 6
            vec_len = 4

        if not (channel_type == 6 and fcu.array_index > 0):
            if timecoded:
                channel = TimeCodedAnimationChannel(
                    vector_len=vec_len,
                    type=channel_type,
                    pivot=pivot_index,
                    time_codes=[])

                num_keyframes = len(fcu.keyframe_points)
                channel.time_codes = [None] * num_keyframes
                channel.num_time_codes = num_keyframes
            else:
                range_ = fcu.range()

                if is_visibility(fcu):
                    channel = AnimationBitChannel()
                else:
                    channel = AnimationChannel(
                        vector_len=vec_len,
                        type=channel_type)

                channel.data = []
                channel.pivot = pivot_index
                num_frames = range_[1] + 1 - range_[0]
                if num_frames == 1:
                    channel.first_frame = bpy.context.scene.frame_start
                    channel.last_frame = bpy.context.scene.frame_end
                else:
                    channel.first_frame = int(range_[0])
                    channel.last_frame = int(range_[1])
                num_frames = channel.last_frame + 1 - channel.first_frame
                channel.data = [None] * num_frames

        if timecoded:
            for i, keyframe in enumerate(fcu.keyframe_points):
                frame = int(keyframe.co.x)
                val = keyframe.co.y

                if channel_type < 6:
                    channel.time_codes[i] = TimeCodedDatum(
                        time_code=frame,
                        value=val)
                else:
                    if channel.time_codes[i] is None:
                        channel.time_codes[i] = TimeCodedDatum(
                            time_code=frame,
                            value=Quaternion())
                    channel.time_codes[i].value[fcu.array_index] = val
        else:
            for frame in range(channel.first_frame, channel.last_frame + 1):
                val = fcu.evaluate(frame)
                i = frame - channel.first_frame

                if is_visibility(fcu) or channel_type < 6:
                    channel.data[i] = val
                else:
                    if channel.data[i] is None:
                        channel.data[i] = Quaternion((1.0, 0.0, 0.0, 0.0))
                    channel.data[i][fcu.array_index] = val

        if channel_type < 6 or fcu.array_index == 3 or is_visibility(fcu):
            channels.append(channel)
    return channels


def retrieve_animation(animation_name, hierarchy, rig, timecoded):
    ani_struct = None
    channels = []

    for mesh in get_objects('MESH'):
        channels.extend(retrieve_channels(
            mesh, hierarchy, timecoded, mesh.name))

    for armature in get_objects('ARMATURE'):
        channels.extend(retrieve_channels(armature, hierarchy, timecoded))

    if timecoded:
        ani_struct = CompressedAnimation(time_coded_channels=channels)
        ani_struct.header.flavor = TIME_CODED_FLAVOR
    else:
        ani_struct = Animation(channels=channels)

    ani_struct.header.name = animation_name
    ani_struct.header.hierarchy_name = hierarchy.name()

    start_frame = bpy.context.scene.frame_start
    end_frame = bpy.context.scene.frame_end

    ani_struct.header.num_frames = end_frame + 1 - start_frame
    ani_struct.header.frame_rate = bpy.context.scene.render.fps
    return ani_struct


##########################################################################
# Helper methods
##########################################################################


def triangulate(mesh):
    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)
    bmesh.ops.triangulate(b_mesh, faces=b_mesh.faces)
    b_mesh.to_mesh(mesh)
    b_mesh.free()


def vertices_to_vectors(vertices):
    vectors = []
    for vert in vertices:
        vectors.append(Vector(vert.co.xyz))
    return vectors


def distance(vec1, vec2):
    x = (vec1.x - vec2.x) ** 2
    y = (vec1.y - vec2.y) ** 2
    z = (vec1.z - vec2.z) ** 2
    return (x + y + z) ** (1 / 2)


def find_most_distant_point(vertex, vertices):
    result = vertices[0]
    dist = 0
    for x in vertices:
        curr_dist = distance(x, vertex)
        if curr_dist > dist:
            dist = curr_dist
            result = x
    return result


def validate_all_points_inside_sphere(center, radius, vertices):
    for vertex in vertices:
        curr_dist = distance(vertex, center)
        if curr_dist > radius:
            delta = (curr_dist - radius) / 2
            radius += delta
            center += (vertex - center).normalized() * delta
    return (center, radius)


def calculate_mesh_sphere(mesh):
    vertices = vertices_to_vectors(mesh.vertices)
    x = find_most_distant_point(vertices[0], vertices)
    y = find_most_distant_point(x, vertices)
    z = (x - y) / 2
    center = y + z
    radius = z.length

    return validate_all_points_inside_sphere(center, radius, vertices)
