# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.utils import *
from io_mesh_w3d.struct import Struct

from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3d.structs.mesh_structs.material_pass import *
from io_mesh_w3d.w3d.structs.mesh_structs.material_info import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *
from io_mesh_w3d.w3d.structs.mesh_structs.triangle import *
from io_mesh_w3d.w3d.structs.mesh_structs.aabbtree import *
from io_mesh_w3d.w3d.structs.mesh_structs.shader import *
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_influence import *
from io_mesh_w3d.w3d.structs.mesh_structs.shader_material import *
from io_mesh_w3d.w3d.structs.mesh_structs.texture import *


W3D_CHUNK_MESH_HEADER = 0x0000001F

# Geometry types
GEOMETRY_TYPE_NORMAL = 0x00000000
GEOMETRY_TYPE_CAMERA_ALIGNED = 0x00010000
GEOMETRY_TYPE_SKIN = 0x00020000

# Prelit types
PRELIT_MASK = 0x0F000000
PRELIT_UNLIT = 0x01000000
PRELIT_VERTEX = 0x02000000
PRELIT_LIGHTMAP_MULTI_PASS = 0x04000000
PRELIT_LIGHTMAP_MULTI_TEXTURE = 0x08000000

# Vertex channels
VERTEX_CHANNEL_LOCATION = 0x01
VERTEX_CHANNEL_NORMAL = 0x02
VERTEX_CHANNEL_TANGENT = 0x20
VERTEX_CHANNEL_BITANGENT = 0x40


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
    vert_channel_flags = 0
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
        write_chunk_head(W3D_CHUNK_MESH_HEADER, io_stream,
                         self.size(False))
        self.version.write(io_stream)
        write_ulong(self.attrs, io_stream)
        write_fixed_string(self.mesh_name, io_stream)
        write_fixed_string(self.container_name, io_stream)
        write_ulong(self.face_count, io_stream)
        write_ulong(self.vert_count, io_stream)
        write_ulong(self.matl_count, io_stream)
        write_ulong(self.damage_stage_count, io_stream)
        write_ulong(self.sort_level, io_stream)
        write_ulong(self.prelit_version, io_stream)
        write_ulong(self.future_count, io_stream)
        write_ulong(self.vert_channel_flags, io_stream)
        write_ulong(self.face_channel_flags, io_stream)
        write_vector(self.min_corner, io_stream)
        write_vector(self.max_corner, io_stream)
        write_vector(self.sph_center, io_stream)
        write_float(self.sph_radius, io_stream)


W3D_CHUNK_MESH = 0x00000000
W3D_CHUNK_VERTICES = 0x00000002
W3D_CHUNK_VERTICES_2 = 0xC00
W3D_CHUNK_VERTEX_NORMALS = 0x00000003
W3D_CHUNK_NORMALS_2 = 0xC01
W3D_CHUNK_MESH_USER_TEXT = 0x0000000C
W3D_CHUNK_VERTEX_INFLUENCES = 0x0000000E
W3D_CHUNK_TRIANGLES = 0x00000020
W3D_CHUNK_VERTEX_SHADE_INDICES = 0x00000022
W3D_CHUNK_SHADER_MATERIALS = 0x50
W3D_CHUNK_TANGENTS = 0x60
W3D_CHUNK_BITANGENTS = 0x61


class Mesh(Struct):
    header = MeshHeader()
    user_text = ""
    verts = []
    normals = []
    tangents = []
    bitangents = []
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
    prelit_unlit = None
    prelit_vertex = None
    prelit_lightmap_multi_pass = None
    prelit_lightmap_multi_texture = None

    def is_skin(self):
        return (self.header.attrs & GEOMETRY_TYPE_SKIN) > 0

    def has_prelit_vertex(self):
        return (self.header.attrs & PRELIT_VERTEX) > 0

    def name(self):
        return self.header.mesh_name

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Mesh(
            verts=[],
            normals=[],
            tangents=[],
            bitangents=[],
            vert_infs=[],
            triangles=[],
            shade_ids=[],
            mat_info=None,
            shaders=[],
            vert_materials=[],
            textures=[],
            material_passes=[],
            shader_materials=[],
            aabbtree=None,
            prelit_unlit=None,
            prelit_vertex=None,
            prelit_lightmap_multi_pass=None,
            prelit_lightmap_multi_texture=None)

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
                    context, io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_SHADER_MATERIALS:
                result.shader_materials = read_chunk_array(
                    context, io_stream, subchunk_end, W3D_CHUNK_SHADER_MATERIAL, ShaderMaterial.read)
            elif chunk_type == W3D_CHUNK_TANGENTS:
                #print("-> tangents are computed in blender")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_BITANGENTS:
                #print("-> bitangents are computed in blender")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_AABBTREE:
                result.aabbtree = AABBTree.read(
                    context, io_stream, subchunk_end)
            elif chunk_type == W3D_CHUNK_PRELIT_UNLIT:
                result.prelit_unlit = PrelitBase.read(
                    context, io_stream, subchunk_end,
                    chunk_type)
            elif chunk_type == W3D_CHUNK_PRELIT_VERTEX:
                result.prelit_vertex = PrelitBase.read(
                    context, io_stream, subchunk_end,
                    chunk_type)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS:
                result.prelit_lightmap_multi_pass = PrelitBase.read(
                    context, io_stream, subchunk_end,
                    chunk_type)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE:
                result.prelit_lightmap_multi_texture = PrelitBase.read(
                    context, io_stream, subchunk_end,
                    chunk_type)
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
        size += vec_list_size(self.tangents)
        size += vec_list_size(self.bitangents)
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
        if self.prelit_unlit is not None:
            size += self.prelit_unlit.size()
        if self.prelit_vertex is not None:
            size += self.prelit_vertex.size()
        if self.prelit_lightmap_multi_pass is not None:
            size += self.prelit_lightmap_multi_pass.size()
        if self.prelit_lightmap_multi_texture is not None:
            size += self.prelit_lightmap_multi_texture.size()
        return size


    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_MESH, io_stream,
                         self.size(), has_sub_chunks=True)
        self.header.write(io_stream)

        if len(self.user_text):
            write_chunk_head(
                W3D_CHUNK_MESH_USER_TEXT, io_stream, text_size(self.user_text, False))
            write_string(self.user_text, io_stream)

        write_chunk_head(W3D_CHUNK_VERTICES, io_stream,
                         vec_list_size(self.verts, False))
        write_list(self.verts, io_stream, write_vector)

        write_chunk_head(W3D_CHUNK_VERTEX_NORMALS, io_stream,
                         vec_list_size(self.normals, False))
        write_list(self.normals, io_stream, write_vector)

        if self.tangents:
            write_chunk_head(W3D_CHUNK_TANGENTS, io_stream,
                             vec_list_size(self.tangents, False))
            write_list(self.tangents, io_stream, write_vector)

        if self.bitangents:
            write_chunk_head(W3D_CHUNK_BITANGENTS, io_stream,
                             vec_list_size(self.bitangents, False))
            write_list(self.bitangents, io_stream, write_vector)

        write_chunk_head(W3D_CHUNK_TRIANGLES, io_stream,
                         list_size(self.triangles, False))
        write_list(self.triangles, io_stream, Triangle.write)

        if self.vert_infs:
            write_chunk_head(W3D_CHUNK_VERTEX_INFLUENCES, io_stream,
                             list_size(self.vert_infs, False))
            write_list(self.vert_infs, io_stream, VertexInfluence.write)

        if self.shade_ids:
            write_chunk_head(
                W3D_CHUNK_VERTEX_SHADE_INDICES, io_stream,
                long_list_size(self.shade_ids, False))
            write_list(self.shade_ids, io_stream, write_long)

        if self.mat_info is not None:
            self.mat_info.write(io_stream)

        if self.vert_materials:
            write_chunk_head(W3D_CHUNK_VERTEX_MATERIALS, io_stream,
                             list_size(self.vert_materials, False), has_sub_chunks=True)
            write_list(self.vert_materials, io_stream,
                       VertexMaterial.write)

        if self.shaders:
            write_chunk_head(W3D_CHUNK_SHADERS, io_stream,
                             list_size(self.shaders, False))
            write_list(self.shaders, io_stream, Shader.write)

        if self.textures:
            write_chunk_head(W3D_CHUNK_TEXTURES, io_stream,
                             list_size(self.textures, False), has_sub_chunks=True)
            write_list(self.textures, io_stream, Texture.write)

        if self.shader_materials:
            write_chunk_head(W3D_CHUNK_SHADER_MATERIALS, io_stream,
                             list_size(self.shader_materials, False), has_sub_chunks=True)
            write_list(self.shader_materials, io_stream,
                       ShaderMaterial.write)

        if self.material_passes:
            write_list(self.material_passes, io_stream,
                       MaterialPass.write)

        if self.aabbtree is not None:
            self.aabbtree.write(io_stream)

        if self.prelit_unlit is not None:
            self.prelit_unlit.write(io_stream)

        if self.prelit_vertex is not None:
            self.prelit_vertex.write(io_stream)

        if self.prelit_lightmap_multi_pass is not None:
            self.prelit_lightmap_multi_pass.write(io_stream)

        if self.prelit_lightmap_multi_texture is not None:
            self.prelit_lightmap_multi_texture.write(io_stream)


##########################################################################
# Unsupported
##########################################################################


W3D_CHUNK_DEFORM = 0x00000058
W3D_CHUNK_PS2_SHADERS = 0x00000080
