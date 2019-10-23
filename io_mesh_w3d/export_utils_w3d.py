# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

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

from io_mesh_w3d.structs.w3d_material import USE_DEPTH_CUE, ARGB_EMISSIVE_ONLY, \
    COPY_SPECULAR_TO_DIFFUSE, DEPTH_CUE_TO_ALPHA


def get_mesh_objects():
    return [object for object in bpy.context.scene.objects if object.type == 'MESH']


#######################################################################################
# Mesh data
#######################################################################################


def retrieve_boundingboxes(container_name):
    boxes = []
    mesh_objects = get_mesh_objects()

    #TODO: append box to hlod?
    for mesh_object in mesh_objects:
        if mesh_object.name == "BOUNDINGBOX":
            box = Box(
                name=container_name + "." + mesh_object.name,
                center=mesh_object.location)
            box_mesh = mesh_object.to_mesh(
                preserve_all_data_layers=False, depsgraph=None)
            box.extend = Vector(
                (box_mesh.vertices[0].co.x * 2, box_mesh.vertices[0].co.y * 2, box_mesh.vertices[0].co.z))
            boxes.append(box)
    return boxes


def retrieve_meshes(skn_file, hierarchy, rig, hlod, container_name):
    mesh_structs = []
    mesh_objects = get_mesh_objects()

    for mesh_object in mesh_objects:
        if mesh_object.name == "BOUNDINGBOX":
            continue

        mesh_struct = Mesh(
            verts=[],
            normals=[],
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

        for vertex in mesh.vertices:
            vertInf = VertexInfluence()

            if vertex.groups:
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

                elif len(vertex.groups) > 2:
                    print("Error: max 2 bone influences per vertex supported!")

            if not vertex.groups:
                mesh_struct.verts.append(vertex.co.xyz)

            mesh_struct.normals.append(vertex.normal)

        header.min_corner = Vector(
            (mesh_object.bound_box[0][0], mesh_object.bound_box[0][1], mesh_object.bound_box[0][2]))
        header.max_corner = Vector(
            (mesh_object.bound_box[6][0], mesh_object.bound_box[6][1], mesh_object.bound_box[6][2]))

        for face in mesh.polygons:
            triangle = Triangle()
            triangle.vert_ids = [face.vertices[0],
                                    face.vertices[1], face.vertices[2]]
            triangle.normal = Vector(face.normal)
            vec1 = mesh.vertices[face.vertices[0]].co.xyz
            vec2 = mesh.vertices[face.vertices[1]].co.xyz
            vec3 = mesh.vertices[face.vertices[2]].co.xyz
            tri_pos = Vector((vec1 + vec2 + vec3)) / 3.0
            triangle.distance = (mesh_object.location - tri_pos).length
            mesh_struct.triangles.append(triangle)

        if mesh_object.vertex_groups:
            header.attrs = GEOMETRY_TYPE_SKIN

        center, radius = calculate_mesh_sphere(mesh)
        header.sphCenter = center
        header.sphRadius = radius

        header.faceCount = len(mesh_struct.triangles)

        # HLod stuff
        subObject = HLodSubObject()
        subObject.name = container_name + "." + mesh_object.name
        subObject.bone_index = 0

        if header.attrs == GEOMETRY_TYPE_SKIN:
            for index, pivot in enumerate(hierarchy.pivots):
                if pivot.name == mesh_object.name:
                    subObject.bone_index = index
        hlod.lod_array.sub_objects.append(subObject)

        for material in mesh.materials:
            mesh_struct.shaders.append(create_shader(material))

            #principled = get_principled_bsdf(material)
            #if principled.normalmap_tex is not None:
            #    mesh_struct.shader_materials.append(create_shader_material(material, principled))
            #else:
            #    mesh_struct.vert_materials.append(create_vertex_material(material))

            #    if principled.diffuse_tex is not None:
            #        info = TextureInfo(
            #            attributes=0,
            #            animation_type=0,
            #            frame_count=0, 
            #            frame_rate=0.0)
            #        tex = Texture(
            #            name=principled.diffuse_tex,
            #            tex_info=info)
            #        mesh_struct.textures.append(tex)

        mesh_struct.mat_info = MaterialInfo(
            pass_count=len(mesh_struct.material_passes),
            vert_matl_count=len(mesh_struct.vert_materials),
            shader_count=len(mesh_struct.shaders),
            texture_count=len(mesh_struct.textures))

        mesh_structs.append(mesh_struct)
    return mesh_structs


#######################################################################################
# material data
#######################################################################################

class PrincipledBSDF(Struct):
    base_color = None
    alpha = None
    diffuse_tex = None
    normalmap_tex = None
    bump_scale = None


def vector_to_rgba(vec):
    return RGBA(r=int(vec[0] * 255), g=int(vec[1] * 255), b=int(vec[2] * 255), a=0)


def get_principled_bsdf(material):
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


def create_vertex_material(material):
    info = VertexMaterialInfo(
        attributes=0,
        shininess=material.specular_intensity,
        specular=vector_to_rgba(material.specular_color),
        diffuse=vector_to_rgba(material.diffuse_color),
        emissive=vector_to_rgba(material.emission),
        ambient=vector_to_rgba(material.ambient),
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
        vm_name=material.name.split('.')[1],
        vm_info=info,
        vm_args_0=material.vm_args_0,
        vm_args_1=material.vm_args_1)

    return vert_material


def append_property(properties, type, name, value):
    properties.append(ShaderMaterialProperty(type=type, name=name, value=value))


def create_shader_material(material, principled):
    shader_material = ShaderMaterial(
        # TODO: do those values have any meaning?
        header=ShaderMaterialHeader(
            number=55,
            type_name="headerType"),
        properties=[])

    principled = get_principled_bsdf(material)

    if principled.diffuse_tex is not None:
        append_property(shader_material.properties, 1, "DiffuseTexture", principled.diffuse_tex)

    if principled.normalmap_tex is not None:
        append_property(shader_material.properties, 1, "NormalMap", principled.normalmap_tex)

    if principled.bump_scale is not None:
        append_property(shader_material.properties, 2, "BumpScale", principled.bump_scale)

    append_property(shader_material.properties, 2, "SpecularExponent", material.specular_intensity)
    append_property(shader_material.properties, 5, "AmbientColor", vector_to_rgba(material.ambient))
    append_property(shader_material.properties, 5, "DiffuseColor", vector_to_rgba(material.diffuse_color))
    append_property(shader_material.properties, 5, "SpecularColor", vector_to_rgba(material.specular_color))
    append_property(shader_material.properties, 7, "AlphaTestEnable", int(material.alpha_test))

    return shader_material


#######################################################################################
# hierarchy data
#######################################################################################


def create_shader(material):
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


#######################################################################################
# hierarchy data
#######################################################################################


def retrieve_hierarchy(container_name):
    hierarchy = Hierarchy(
        header=HierarchyHeader(),
        pivots=[])
    root = HierarchyPivot(
        name="ROOTTRANSFORM",
        parentID=-1)

    rig = None
    hierarchy.pivots.append(root)

    rigs = [object for object in bpy.context.scene.objects if object.type == 'ARMATURE']

    if len(rigs) > 1:
        print("Error: only one armature per scene allowed")
        return

    if len(rigs) == 1:
        rig = rigs[0]
        hierarchy.header.name = rig.name
        for bone in rig.pose.bones:
            pivot = HierarchyPivot(
                name=bone.name,
                parent_id=0)

            matrix = bone.matrix

            if bone.parent is not None:
                for index, piv in enumerate(hierarchy.pivots):
                    if piv.name == bone.parent.name:
                        pivot.parent_id = index
                matrix = bone.parent.matrix.inverted() @ matrix

            (pivot.translation, pivot.rotation, _) = matrix.decompose()

            hierarchy.pivots.append(pivot)
    else:
        hierarchy.header.name = container_name

    mesh_objects = [
        object for object in bpy.context.scene.objects if object.type == 'MESH']

    for mesh_object in mesh_objects:
        # TODO: use a constant here
        if not mesh_object.vertex_groups and mesh_object.name != "BOUNDINGBOX":
            pivot = HierarchyPivot(
                name=mesh_object.name,
                parent_id=0,
                translation=mesh_object.location,
                rotation=mesh_object.rotation_quaternion)

            if mesh_object.parent_bone != "":
                for index, piv in enumerate(hierarchy.pivots):
                    if piv.name == mesh_object.parent_bone:
                        pivot.parent_id = index

            hierarchy.pivots.append(pivot)

    hierarchy.header.num_pivots = len(hierarchy.pivots)

    return (hierarchy, rig)


#######################################################################################
# Animation data
#######################################################################################


def export_animation(ani_file, animation_name, hierarchy):
    # only time coded compression for now
    ani_struct = CompressedAnimation(time_coded_channels=[])
    ani_struct.header.name = animation_name
    ani_struct.header.flavor = 0 # time coded
    ani_struct.header.hierarchy_name = hierarchy.header.name

    start_frame = bpy.data.scenes["Scene"].frame_start
    end_frame = bpy.data.scenes["Scene"].frame_end

    ani_struct.header.num_frames = end_frame + 1 - start_frame
    ani_struct.header.frame_rate = bpy.data.scenes["Scene"].render.fps

    if len(bpy.data.actions) > 1:
        print("Error: too many actions in scene")

    channel = None

    action = bpy.data.actions[0]
    for fcu in action.fcurves:
        pivot_name = fcu.data_path.split('"')[1]
        pivot_index = 0
        for i, pivot in enumerate(hierarchy.pivots):
            if pivot.name == pivot_name:
                pivot_index = i

        channel_type = 0
        vec_len = 1
        index = fcu.array_index
        if "rotation_quaternion" in fcu.data_path:
            channel_type = 6
            vec_len = 4
        else:
            channel_type = index

        if not (channel_type == 6 and index > 0):
            channel = TimeCodedAnimationChannel(
                vector_len=vec_len,
                type=channel_type,
                pivot=pivot_index,
                time_codes=[])

            num_keyframes = len(fcu.keyframe_points)
            channel.time_codes = [None] * num_keyframes
            channel.num_time_codes = num_keyframes
            channel.first_frame = int(fcu.keyframe_points[0].co.x)
            channel.last_frame = int(fcu.keyframe_points[num_keyframes - 1].co.x)

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

        if channel_type < 6 or index == 3:
            ani_struct.time_coded_channels.append(channel)

    ani_struct.write(ani_file)
    return ani_struct


#######################################################################################
# Helper methods
#######################################################################################


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
    return (x + y + z)**(1/2)


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
            delta = (curr_dist - radius)/2
            radius += delta
            center += (vertex - center).normalized() * delta
    return (center, radius)


def calculate_mesh_sphere(mesh):
    vertices = vertices_to_vectors(mesh.vertices)
    x = find_most_distant_point(vertices[0], vertices)
    y = find_most_distant_point(x, vertices)
    z = (x - y)/2
    center = y + z
    radius = z.length

    return validate_all_points_inside_sphere(center, radius, vertices)
