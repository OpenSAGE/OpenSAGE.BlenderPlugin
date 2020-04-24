# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh
from bpy_extras import node_shader_utils

from io_mesh_w3d.common.shading.vertex_material_group import *
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.w3d.structs.mesh_structs.prelit import PrelitBase
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *


def get_or_create_uv_layer(mesh, b_mesh, triangles, tx_coords):
    if tx_coords is None:
        return

    for uv_layer in mesh.uv_layers:
        uv_layer_exists = True
        for i, face in enumerate(b_mesh.faces):
            for loop in face.loops:
                idx = triangles[i][loop.index % 3]
                if uv_layer.data[loop.index].uv != tx_coords[idx].xy:
                    uv_layer_exists = False
        if uv_layer_exists:
            return uv_layer.name

    uv_layer = mesh.uv_layers.new(do_init=False)
    for i, face in enumerate(b_mesh.faces):
        for loop in face.loops:
            idx = triangles[i][loop.index % 3]
            uv_layer.data[loop.index].uv = tx_coords[idx].xy

    return uv_layer.name

class PipelineSet():
    def __init__(self):
        self.pipelines = []

    def add(self, set):
        self.pipelines.append(set)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Pipeline():
    def __init__(self, type='', pass_index=0, vert_mat=None, shader=None, texture=None, shader_mat=None, uv_map=None):
        self.type = type
        self.pass_index = pass_index
        self.vert_mat = vert_mat
        self.shader = shader
        self.texture = texture
        self.shader_mat = shader_mat
        self.uv_map = uv_map

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


def expand(ids, count):
    if len(ids) != count:
        return [ids[0]] * count
    return ids


def create_materials(context, structs, mesh, triangles):
    b_mesh = bmesh.new()
    b_mesh.from_mesh(mesh)

    num_faces = len(triangles)
    face_pipeline_sets = [None] * num_faces

    for struct in structs:
        if struct is None:
            continue

        for i, mat_pass in enumerate(struct.material_passes):
            vert_mat_ids = [None] * num_faces
            shader_ids = [None] * num_faces
            texture_ids = []
            uv_maps = []
            shader_mat_ids = [None] * num_faces

            if mat_pass.vertex_material_ids:
                vert_mat_ids = expand(mat_pass.vertex_material_ids, num_faces)

            if mat_pass.shader_ids:
                shader_ids = expand(mat_pass.shader_ids, num_faces)

            if mat_pass.shader_material_ids:
                shader_mat_ids = expand(mat_pass.shader_material_ids, num_faces)

            if mat_pass.tx_coords:
                uv_maps = get_or_create_uv_layer(mesh, b_mesh, triangles, mat_pass.tx_coords)

            for tx_stage in mat_pass.tx_stages:
                for tx_coords in tx_stage.tx_coords:
                    uv_maps.append(get_or_create_uv_layer(mesh, b_mesh, triangles, tx_coords))

                type = 'vertex'
                if isinstance(struct, PrelitBase):
                    type += '_' + str(struct.type)

                for k, tx_ids in enumerate(tx_stage.tx_ids):
                    tex_ids = expand(tx_ids, num_faces)
                    uv_map = uv_maps[k]
                    for j, tri in enumerate(triangles):
                        pipeline = Pipeline(
                            type=type,
                            pass_index=i,
                            vert_mat=struct.vert_materials[vert_mat_ids[j]],
                            shader=struct.shaders[shader_ids[j]],
                            texture=struct.textures[tex_ids[j]],
                            uv_map=uv_map)

                        if face_pipeline_sets[j] is None:
                            face_pipeline_sets[j] = PipelineSet()
                        face_pipeline_sets[j].add(pipeline)

            if not isinstance(struct, PrelitBase) and struct.shader_materials:
                for j, tri in enumerate(triangles):
                    pipeline = Pipeline(
                        type='shader',
                        pass_index=i,
                        shader_mat=struct.shader_materials[shader_mat_ids[j]],
                        uv_map=uv_maps)

                    if face_pipeline_sets[j] is None:
                        face_pipeline_sets[j] = PipelineSet()
                    face_pipeline_sets[j].add(pipeline)

    unique_pipeline_sets = []
    face_mat_indices = [0] * num_faces

    for i, pipeline_set in enumerate(face_pipeline_sets):
        if pipeline_set in unique_pipeline_sets:
            face_mat_indices[i] = unique_pipeline_sets.index(pipeline_set)
        else:
            unique_pipeline_sets.append(pipeline_set)

    for pps in unique_pipeline_sets:
        create_material(context, mesh, b_mesh, triangles, pps)

    for i, polygon in enumerate(mesh.polygons):
        polygon.material_index = face_mat_indices[i]

    b_mesh.free()


def create_material(context, mesh, b_mesh, triangles, pps):
    material = bpy.data.materials.new(mesh.name)
    mesh.materials.append(material)

    material.use_nodes = True
    material.shadow_method = 'CLIP'
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    node_tree = material.node_tree
    node_tree.nodes.remove(node_tree.nodes.get('Principled BSDF'))

    vert_ = dict()
    uv_nodes = dict()
    uv_tex_combos = dict()

    for pipeline in pps.pipelines:
        if 'vertex' in pipeline.type:
            create_vertex_material_pipeline(context, node_tree, pipeline, vert_, uv_nodes, uv_tex_combos)
        else:
            create_shader_material_pipeline(context, node_tree, pipeline)


##########################################################################
# vertex material
##########################################################################

def create_vertex_material_pipeline(context, node_tree, pipeline, vert_, uv_nodes, uv_tex_combos):
    instance = VertexMaterialGroup.create(node_tree, pipeline.vert_mat, pipeline.shader)
    instance.label = pipeline.vert_mat.vm_name + '_' + str(pipeline.pass_index) + '_' + str(pipeline.type)
    instance.location = (0, 300)
    instance.width = 200
    instance.hide = True

    output = node_tree.nodes.get('Material Output')

    links = node_tree.links
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])

    if pipeline.texture is not None:
        if (pipeline.uv_map, pipeline.texture.file) in uv_tex_combos:
            texture_node = uv_tex_combos[(pipeline.uv_map, pipeline.texture.file)]
        else:
            texture = find_texture(context, pipeline.texture.file, pipeline.texture.id)
            texture_node = node_tree.nodes.new('ShaderNodeTexImage')
            texture_node.image = texture
            texture_node.location = (-350, 300 * (-len(uv_tex_combos) + 1))
            texture_node.hide = True
            uv_tex_combos[(pipeline.uv_map, pipeline.texture.file)] = texture_node

        links.new(texture_node.outputs['Color'], instance.inputs['DiffuseTexture'])
        links.new(texture_node.outputs['Alpha'], instance.inputs['DiffuseTextureAlpha'])

        if pipeline.uv_map in uv_nodes:
            uv_node = uv_nodes[pipeline.uv_map]
        else:
            uv_node = node_tree.nodes.new('ShaderNodeUVMap')
            uv_node.location = (-550, 300 * (-len(uv_nodes) + 1))
            uv_node.uv_map = pipeline.uv_map
            uv_nodes[pipeline.uv_map] = uv_node

        links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])


##########################################################################
# shader material
##########################################################################


def create_shader_material_pipeline(context, node_tree, pipeline):
    mat_name = pipeline.shader_mat.header.type_name

    instance = node_tree.nodes.new(type='ShaderNodeGroup')
    instance.node_tree = bpy.data.node_groups[mat_name]
    instance.label = mat_name
    instance.location = (0, 300)
    instance.width = 200

    links = node_tree.links

    if pipeline.shader_mat.header.technique is not None:
        instance.inputs['Technique'].default_value = pipeline.shader_mat.header.technique

    y = 300
    for prop in pipeline.shader_mat.properties:
        if prop.type == STRING_PROPERTY and prop.value != '':
            texture_node = node_tree.nodes.new('ShaderNodeTexImage')
            texture_node.image = find_texture(context, prop.value)
            texture_node.location = (-350, y)

            links.new(texture_node.outputs['Color'], instance.inputs[prop.name])
            index = instance.inputs.keys().index(prop.name)
            links.new(texture_node.outputs['Alpha'], instance.inputs[index + 1])

            uv_node = node_tree.nodes.new('ShaderNodeUVMap')
            uv_node.location = (-550, y)
            uv_node.uv_map = pipeline.uv_map
            links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
            y -= 300

        elif prop.type == VEC4_PROPERTY:
            instance.inputs[prop.name].default_value = prop.to_rgba()
        else:
            instance.inputs[prop.name].default_value = prop.value

    output = node_tree.nodes.get('Material Output')
    links.new(instance.outputs['BSDF'], output.inputs['Surface'])
