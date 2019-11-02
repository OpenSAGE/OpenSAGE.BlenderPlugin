# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_material_pass import *
from io_mesh_w3d.structs.w3d_material_info import *
from io_mesh_w3d.structs.w3d_vertex_material import *
from io_mesh_w3d.structs.w3d_triangle import *
from io_mesh_w3d.structs.w3d_aabbtree import *
from io_mesh_w3d.structs.w3d_shader import *
from io_mesh_w3d.structs.w3d_vertex_influence import *
from io_mesh_w3d.structs.w3d_shader_material import *
from io_mesh_w3d.structs.w3d_texture import *
from io_mesh_w3d.import_utils_w3d import *
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.utils import *


W3D_CHUNK_MESH_HEADER = 0x0000001F
GEOMETRY_TYPE_SKIN = 0x00020000


class MeshHeader(Struct):
    version = Version()
    attrs = 0
    mesh_name = ""
    container_name = ""
    face_count = 0
    vert_count = 0
    matl_count = 0
    damage_stage_count = 0
    sort_level = 0
    prelit_version = 0
    future_count = 0
    vert_channel_flags = 3
    face_channel_flags = 1
    min_corner = Vector((0.0, 0.0, 0.0))
    max_corner = Vector((0.0, 0.0, 0.0))
    sph_center = Vector((0.0, 0.0, 0.0))
    sph_radius = 0.0

    @staticmethod
    def read(io_stream):
        return MeshHeader(
            version=Version.read(io_stream),
            attrs=read_ulong(io_stream),
            mesh_name=read_fixed_string(io_stream),
            container_name=read_fixed_string(io_stream),
            face_count=read_ulong(io_stream),
            vert_count=read_ulong(io_stream),
            matl_count=read_ulong(io_stream),
            damage_stage_count=read_ulong(io_stream),
            sort_level=read_ulong(io_stream),
            prelit_version=read_ulong(io_stream),
            future_count=read_ulong(io_stream),
            vert_channel_flags=read_ulong(io_stream),
            face_channel_flags=read_ulong(io_stream),
            # bounding volumes
            min_corner=read_vector(io_stream),
            max_corner=read_vector(io_stream),
            sph_center=read_vector(io_stream),
            sph_radius=read_float(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(116, include_head)

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_MESH_HEADER,
                         self.size(False))
        self.version.write(io_stream)
        write_ulong(io_stream, self.attrs)
        write_fixed_string(io_stream, self.mesh_name)
        write_fixed_string(io_stream, self.container_name)
        write_ulong(io_stream, self.face_count)
        write_ulong(io_stream, self.vert_count)
        write_ulong(io_stream, self.matl_count)
        write_ulong(io_stream, self.damage_stage_count)
        write_ulong(io_stream, self.sort_level)
        write_ulong(io_stream, self.prelit_version)
        write_ulong(io_stream, self.future_count)
        write_ulong(io_stream, self.vert_channel_flags)
        write_ulong(io_stream, self.face_channel_flags)
        write_vector(io_stream, self.min_corner)
        write_vector(io_stream, self.max_corner)
        write_vector(io_stream, self.sph_center)
        write_float(io_stream, self.sph_radius)


W3D_CHUNK_MESH = 0x00000000
W3D_CHUNK_VERTICES = 0x00000002
W3D_CHUNK_VERTICES_2 = 0xC00
W3D_CHUNK_VERTEX_NORMALS = 0x00000003
W3D_CHUNK_NORMALS_2 = 0xC01
W3D_CHUNK_MESH_USER_TEXT = 0x0000000C
W3D_CHUNK_VERTEX_INFLUENCES = 0x0000000E
W3D_CHUNK_TRIANGLES = 0x00000020
W3D_CHUNK_VERTEX_SHADE_INDICES = 0x00000022
W3D_CHUNK_SHADERS = 0x00000029
W3D_CHUNK_VERTEX_MATERIALS = 0x0000002A
W3D_CHUNK_TEXTURES = 0x00000030
W3D_CHUNK_SHADER_MATERIALS = 0x50
W3D_CHUNK_TANGENTS = 0x60
W3D_CHUNK_BITANGENTS = 0x61


class Mesh(Struct):
    header = MeshHeader()
    user_text = ""
    verts = []
    normals = []
    vert_infs = []
    triangles = []
    shade_ids = []
    mat_info = None
    shaders = []
    vert_materials = []
    textures = []
    shader_materials = []
    material_passes = []
    aabbtree = None

    def is_skin(self):
        return (self.header.attrs & GEOMETRY_TYPE_SKIN) > 0

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Mesh(
            verts=[],
            normals=[],
            vert_infs=[],
            triangles=[],
            shade_ids=[],
            mat_info=None,
            shaders=[],
            vert_materials=[],
            textures=[],
            material_passes=[],
            shader_materials=[],
            aabbtree=None)

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_VERTICES:
                result.verts = read_list(io_stream, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_VERTICES_2:
                #print("-> vertices 2 chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_VERTEX_NORMALS:
                result.normals = read_list(
                    io_stream, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_NORMALS_2:
                #print("-> normals 2 chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_MESH_USER_TEXT:
                result.user_text = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_INFLUENCES:
                result.vert_infs = read_list(
                    io_stream, subchunk_end, VertexInfluence.read)
            elif chunk_type == W3D_CHUNK_MESH_HEADER:
                result.header = MeshHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_TRIANGLES:
                result.triangles = read_list(
                    io_stream, subchunk_end, Triangle.read)
            elif chunk_type == W3D_CHUNK_VERTEX_SHADE_INDICES:
                result.shade_ids = read_list(
                    io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_MATERIAL_INFO:
                result.mat_info = MaterialInfo.read(io_stream)
            elif chunk_type == W3D_CHUNK_SHADERS:
                result.shaders = read_list(
                    io_stream, subchunk_end, Shader.read)
            elif chunk_type == W3D_CHUNK_VERTEX_MATERIALS:
                result.vert_materials = read_chunk_array(
                    context,
                    io_stream,
                    subchunk_end,
                    W3D_CHUNK_VERTEX_MATERIAL,
                    VertexMaterial.read)
            elif chunk_type == W3D_CHUNK_TEXTURES:
                result.textures = read_chunk_array(
                    context, io_stream, subchunk_end, W3D_CHUNK_TEXTURE, Texture.read)
            elif chunk_type == W3D_CHUNK_MATERIAL_PASS:
                result.material_passes.append(MaterialPass.read(
                    io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_SHADER_MATERIALS:
                result.shader_materials = read_chunk_array(
                    context, io_stream, subchunk_end, W3D_CHUNK_SHADER_MATERIAL, ShaderMaterial.read)
            elif chunk_type == W3D_CHUNK_TANGENTS:
                #print("-> tangents chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_BITANGENTS:
                #print("-> bitangents chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_AABBTREE:
                result.aabbtree = AABBTree.read(
                    context, io_stream, subchunk_end)
            elif chunk_type == W3D_CHUNK_PRELIT_UNLIT:
                print("-> prelit unlit chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_VERTEX:
                print("-> prelit vertex chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS:
                print("-> prelit lightmap multi pass chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE:
                print("-> prelit lightmap multi texture chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_DEFORM:
                print("-> deform chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PS2_SHADERS:
                print("-> ps2 shaders chunk is not supported")
                io_stream.seek(chunk_size, 1)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self):
        size = self.header.size()
        size += text_size(self.user_text)
        size += vec_list_size(self.verts)
        size += vec_list_size(self.normals)
        size += list_size(self.triangles)
        size += list_size(self.vert_infs)
        size += list_size(self.shaders)
        size += list_size(self.textures)
        size += long_list_size(self.shade_ids)
        size += list_size(self.shader_materials)
        if self.mat_info is not None:
            size += self.mat_info.size()
        size += list_size(self.vert_materials)
        size += list_size(self.material_passes, False)
        if self.aabbtree is not None:
            size += self.aabbtree.size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_MESH,
                         self.size(), has_sub_chunks=True)
        self.header.write(io_stream)

        if len(self.user_text):
            write_chunk_head(
                io_stream, W3D_CHUNK_MESH_USER_TEXT, text_size(self.user_text, False))
            write_string(io_stream, self.user_text)

        write_chunk_head(io_stream, W3D_CHUNK_VERTICES,
                         vec_list_size(self.verts, False))
        write_list(io_stream, self.verts, write_vector)

        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_NORMALS,
                         vec_list_size(self.normals, False))
        write_list(io_stream, self.normals, write_vector)

        write_chunk_head(io_stream, W3D_CHUNK_TRIANGLES,
                         list_size(self.triangles, False))
        write_object_list(io_stream, self.triangles, Triangle.write)

        if self.vert_infs:
            write_chunk_head(io_stream, W3D_CHUNK_VERTEX_INFLUENCES,
                             list_size(self.vert_infs, False))
            write_object_list(io_stream, self.vert_infs, VertexInfluence.write)

        if self.shade_ids:
            write_chunk_head(
                io_stream,
                W3D_CHUNK_VERTEX_SHADE_INDICES,
                long_list_size(self.shade_ids, False))
            write_list(io_stream, self.shade_ids, write_long)

        if self.mat_info is not None:
            self.mat_info.write(io_stream)

        if self.vert_materials:
            write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIALS,
                             list_size(self.vert_materials, False), has_sub_chunks=True)
            write_object_list(io_stream, self.vert_materials,
                              VertexMaterial.write)

        if self.shaders:
            write_chunk_head(io_stream, W3D_CHUNK_SHADERS,
                             list_size(self.shaders, False))
            write_object_list(io_stream, self.shaders, Shader.write)

        if self.textures:
            write_chunk_head(io_stream, W3D_CHUNK_TEXTURES,
                             list_size(self.textures, False), has_sub_chunks=True)
            write_object_list(io_stream, self.textures, Texture.write)

        if self.shader_materials:
            write_chunk_head(io_stream, W3D_CHUNK_SHADER_MATERIALS,
                             list_size(self.shader_materials, False), has_sub_chunks=True)
            write_object_list(io_stream, self.shader_materials,
                              ShaderMaterial.write)

        if self.material_passes:
            write_object_list(io_stream, self.material_passes,
                              MaterialPass.write)

        if self.aabbtree is not None:
            self.aabbtree.write(io_stream)


##########################################################################
# Unsupported
##########################################################################

W3D_CHUNK_PRELIT_UNLIT = 0x00000023
W3D_CHUNK_PRELIT_VERTEX = 0x00000024
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS = 0x00000025
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE = 0x00000026

W3D_CHUNK_DEFORM = 0x00000058
W3D_CHUNK_PS2_SHADERS = 0x00000080
