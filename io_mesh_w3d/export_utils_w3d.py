# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from mathutils import Vector

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.structs.w3d_hlod import *
from io_mesh_w3d.structs.w3d_mesh import *
from io_mesh_w3d.structs.w3d_box import *
from io_mesh_w3d.structs.w3d_shader import *
from io_mesh_w3d.structs.w3d_hierarchy import *
from io_mesh_w3d.structs.w3d_animation import *
from io_mesh_w3d.structs.w3d_compressed_animation import *

bounding_box_names = ["BOUNDINGBOX", "BOUNDING BOX"]
pick_plane_names = ["PICK"]


def get_objects(type):  # MESH, ARMATURE
    return [object for object in bpy.context.scene.objects if object.type == type]


##########################################################################
# Mesh data
##########################################################################


def retrieve_boxes(hlod, hierarchy):
    boxes = []
    container_name = hlod.header.model_name

    for mesh_object in get_objects('MESH'):
        if not mesh_object.name in bounding_box_names:
            continue

        box = Box(
            name=container_name + "." + mesh_object.name,
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

        subObject = HLodSubObject(
            name=container_name + "." + mesh_object.name,
            bone_index=0)

        for index, pivot in enumerate(hierarchy.pivots):
            if pivot.name == mesh_object.parent_bone:
                subObject.bone_index = index

        hlod.lod_array.sub_objects.append(subObject)
        hlod.lod_array.header.model_count = len(hlod.lod_array.sub_objects)
    return boxes


def retrieve_meshes(context, hierarchy, rig, hlod, container_name):
    mesh_structs = []

    for mesh_object in get_objects('MESH'):
        if mesh_object.name in bounding_box_names:
            continue

        mesh_struct = Mesh(
            header=MeshHeader(),
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
            shader_materials=[])

        header = mesh_struct.header
        header.mesh_name = mesh_object.name
        header.container_name = container_name

        mesh = mesh_object.to_mesh(
            preserve_all_data_layers=False, depsgraph=None)
        triangulate(mesh)

        header.vert_count = len(mesh.vertices)

        for i, vertex in enumerate(mesh.vertices):
            if vertex.groups:
                vertInf = VertexInfluence()
                for index, pivot in enumerate(hierarchy.pivots):
                    if pivot.name == mesh_object.vertex_groups[vertex.groups[0].group].name:
                        vertInf.bone_idx = index
                vertInf.bone_inf = vertex.groups[0].weight
                mesh_struct.vert_infs.append(vertInf)

                bone = rig.pose.bones[hierarchy.pivots[vertInf.bone_idx].name]
                mesh_struct.verts.append(
                    bone.matrix.inverted() @ vertex.co.xyz)

                if len(vertex.groups) > 1:
                    for index, pivot in enumerate(hierarchy.pivots):
                        if pivot.name == mesh_object.vertex_groups[vertex.groups[1].group].name:
                            vertInf.xtra_idx = index
                    vertInf.xtra_inf = vertex.groups[1].weight

                if len(vertex.groups) > 2:
                    message = "WARNING: max 2 bone influences per vertex supported!"
                    print(message)
                    context.report({'ERROR'}, message)

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
            mesh_struct.tangents = [Vector] * len(mesh_struct.normals)
            mesh_struct.bitangents = [Vector] * len(mesh_struct.normals)

        for face in mesh.polygons:
            triangle = Triangle()
            triangle.vert_ids = tuple(face.vertices)
            triangle.normal = Vector(face.normal)
            vec1 = mesh.vertices[face.vertices[0]].normal
            vec2 = mesh.vertices[face.vertices[1]].normal
            vec3 = mesh.vertices[face.vertices[2]].normal
            tri_pos = (vec1 + vec2 + vec3) / 3.0
            triangle.distance = tri_pos.length
            mesh_struct.triangles.append(triangle)

            if mesh.uv_layers:
                for vert in [mesh.loops[i] for i in face.loop_indices]:
                    # TODO: compute the mean value from the face-vertex-tangents etc?
                    normal = vert.normal
                    tangent = vert.tangent
                    mesh_struct.tangents[vert.vertex_index] = tangent
                    bitangent = vert.bitangent_sign * normal.cross(tangent)
                    mesh_struct.bitangents[vert.vertex_index] = bitangent

        header.face_count = len(mesh_struct.triangles)

        if mesh_struct.vert_infs:
            header.attrs = GEOMETRY_TYPE_SKIN

        center, radius = calculate_mesh_sphere(mesh)
        header.sphCenter = center
        header.sphRadius = radius

        append_hlod_subObject(hlod, container_name, mesh_struct, hierarchy)

        b_mesh = bmesh.new()
        b_mesh.from_mesh(mesh)

        tx_stages = []
        for i, uv_layer in enumerate(mesh.uv_layers):
            stage = TextureStage(
                tx_ids=[i],
                per_face_tx_coords=[],
                tx_coords=[(0.0, 0.0)] * len(mesh_struct.verts))

            # TODO: find a cleaner way for doing that
            for face in b_mesh.faces:
                for loop in face.loops:
                    face_index = int(loop.index / 3)
                    face_vert_index = loop.index % 3
                    vert_index = mesh_struct.triangles[face_index].vert_ids[face_vert_index]
                    stage.tx_coords[vert_index] = uv_layer.data[loop.index].uv
            tx_stages.append(stage)

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

            principled = retrieve_principled_bsdf(material)

            if principled.normalmap_tex is not None:
                mat_pass.shader_material_ids = [i]
                mat_pass.tx_coords = tx_stages[i].tx_coords
                mesh_struct.shader_materials.append(
                    retrieve_shader_material(material, principled))
            else:
                mesh_struct.shaders.append(retrieve_shader(material))
                mat_pass.shader_ids = [i]
                mat_pass.vertex_material_ids = [i]
                mat_pass.tx_stages.append(tx_stages[i])
                mesh_struct.vert_materials.append(
                    retrieve_vertex_material(material))

                if principled.diffuse_tex is not None:
                    info = TextureInfo(
                        attributes=0,
                        animation_type=0,
                        frame_count=0,
                        frame_rate=0.0)
                    tex = Texture(
                        name=principled.diffuse_tex,
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
    return mesh_structs


##########################################################################
# hlod
##########################################################################


def create_hlod(container_name, hierarchy_name):
    return HLod(
        header=HLodHeader(
            model_name=container_name,
            hierarchy_name=hierarchy_name),
        lod_array=HLodArray(sub_objects=[]))


def append_hlod_subObject(hlod, container_name, mesh_struct, hierarchy):
    name = mesh_struct.header.mesh_name
    subObject = HLodSubObject()
    subObject.name = container_name + "." + name
    subObject.bone_index = 0

    if not mesh_struct.is_skin():
        for index, pivot in enumerate(hierarchy.pivots):
            pivot_name = pivot.name.replace("B_", "").replace("BAT_","")
            actual_name = name.replace("V_", "")
            if pivot_name == actual_name:
                subObject.bone_index = index

    hlod.lod_array.sub_objects.append(subObject)
    hlod.lod_array.header.model_count = len(hlod.lod_array.sub_objects)


##########################################################################
# material data
##########################################################################


class PrincipledBSDF(Struct):
    base_color = None
    alpha = None
    diffuse_tex = None
    normalmap_tex = None
    bump_scale = None


def retrieve_principled_bsdf(material):
    result = PrincipledBSDF()

    principled = PrincipledBSDFWrapper(material, is_readonly=True)
    result.base_color = principled.base_color
    result.alpha = principled.alpha
    diffuse_tex = principled.base_color_texture
    if diffuse_tex and diffuse_tex.image:
        result.diffuse_tex = diffuse_tex.image.name

    normalmap_tex = principled.normalmap_texture
    if normalmap_tex and normalmap_tex.image:
        result.normalmap_tex = normalmap_tex.image.name
        result.bump_scale = principled.normalmap_strength
    return result


def get_material_name(material):
    name = material.name
    if "." in name:
        return name.split('.')[1]
    return name


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
        vm_name=get_material_name(material),
        vm_info=info,
        vm_args_0=material.vm_args_0,
        vm_args_1=material.vm_args_1)

    return vert_material


def append_property(properties, type, name, value):
    properties.append(ShaderMaterialProperty(
        type=type, name=name, value=value))


def retrieve_shader_material(material, principled):
    shader_material = ShaderMaterial(
        header=ShaderMaterialHeader(
            type_name="NormalMapped.fx"),
        properties=[])

    principled = retrieve_principled_bsdf(material)

    if principled.diffuse_tex is not None:
        append_property(shader_material.properties, 1,
                        "DiffuseTexture", principled.diffuse_tex)

    if principled.normalmap_tex is not None:
        append_property(shader_material.properties, 1,
                        "NormalMap", principled.normalmap_tex)

    if principled.bump_scale is not None:
        append_property(shader_material.properties, 2,
                        "BumpScale", principled.bump_scale)

    append_property(shader_material.properties, 2,
                    "SpecularExponent", material.specular_intensity)
    append_property(shader_material.properties, 3,
                    "BumpUVScale", material.bump_uv_scale)
    append_property(
        shader_material.properties,
        4,
        "Sampler_ClampU_ClampV_NoMip_0",
        material.sampler_clamp_uv_no_mip)
    append_property(shader_material.properties, 5,
                    "AmbientColor", RGBA(material.ambient))
    append_property(shader_material.properties, 5, "DiffuseColor",
                    RGBA(material.diffuse_color))
    append_property(shader_material.properties, 5, "SpecularColor",
                    RGBA(material.specular_color, a=0.0))
    append_property(
        shader_material.properties,
        6,
        "BlendMode",
        material.blend_mode)
    append_property(shader_material.properties, 7,
                    "AlphaTestEnable", int(material.alpha_test))

    return shader_material


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


def retrieve_hierarchy(container_name):
    hierarchy = Hierarchy(
        header=HierarchyHeader(),
        pivots=[],
        pivot_fixups=[])

    root = HierarchyPivot(
        name="ROOTTRANSFORM",
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
    else:
        print("Error: only one armature per scene allowed")
        return

    for mesh_object in get_objects('MESH'):
        if mesh_object.vertex_groups \
                or mesh_object.name in bounding_box_names \
                or mesh_object.name in pick_plane_names \
                or "V_" in mesh_object.name:
            continue

        eulers = mesh_object.rotation_quaternion.to_euler()
        pivot = HierarchyPivot(
            name=mesh_object.name,
            parent_id=0,
            translation=mesh_object.location,
            rotation=mesh_object.rotation_quaternion,
            euler_angles=Vector((eulers.x, eulers.y, eulers.z)))

        if mesh_object.parent_bone is not None and mesh_object.parent_bone is not "":
            pivot.parent_id = mesh_object.parent_bone
        elif mesh_object.parent is not None:
            pivot.parent_id = mesh_object.parent.name

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
    return "rotation_quaternion" in fcu.data_path


def is_visibility(fcu):
    return "hide" in fcu.data_path


def retrieve_channels(obj, hierarchy, timecoded, name=None):
    channels = []

    if obj.animation_data is None or obj.animation_data.action is None:
        return channels

    channel = None

    for fcu in obj.animation_data.action.fcurves:
        if name is None:
            values = fcu.data_path.split('"')
            if len(values) == 1:
                pivot_name = "ROOTTRANSFORM"
            else:
                pivot_name = values[1]
        else:
            pivot_name = name

        pivot_index = 0
        for i, pivot in enumerate(hierarchy.pivots):
            if pivot.name == pivot_name:
                pivot_index = i

        index = fcu.array_index
        channel_type = index
        vec_len = 1

        if is_rotation(fcu):
            channel_type = 6
            vec_len = 4

        if not (channel_type == 6 and index > 0):
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
                    channel.time_codes[i].value[index] = val
        else:
            for frame in range(channel.first_frame, channel.last_frame + 1):
                val = fcu.evaluate(frame)
                i = frame - channel.first_frame

                if is_visibility(fcu):
                    channel.data[i] = bool(val)
                elif channel_type < 6:
                    channel.data[i] = val
                else:
                    if channel.data[i] is None:
                        channel.data[i] = Quaternion((1.0, 0.0, 0.0, 0.0))
                    channel.data[i][index] = val

        if channel_type < 6 or index == 3 or is_visibility(fcu):
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
        ani_struct.header.flavor = 0  # time coded
    else:
        ani_struct = Animation(channels=channels)

    ani_struct.header.name = animation_name
    ani_struct.header.hierarchy_name = hierarchy.header.name

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
    x = (vec1.x - vec2.x)**2
    y = (vec1.y - vec2.y)**2
    z = (vec1.z - vec2.z)**2
    return (x + y + z)**(1 / 2)


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
