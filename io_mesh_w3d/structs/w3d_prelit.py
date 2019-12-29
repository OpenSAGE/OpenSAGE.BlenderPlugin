# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.structs.w3d_material_info import *
from io_mesh_w3d.structs.w3d_material_pass import *
from io_mesh_w3d.structs.w3d_vertex_material import *
from io_mesh_w3d.structs.w3d_shader import *
from io_mesh_w3d.structs.w3d_texture import *
from io_mesh_w3d.import_utils_w3d import *

W3D_CHUNK_PRELIT_UNLIT = 0x00000023
W3D_CHUNK_PRELIT_VERTEX = 0x00000024
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS = 0x00000025
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE = 0x00000026


class PrelitBase(Struct):
    type = W3D_CHUNK_PRELIT_UNLIT

    mat_info = MaterialInfo()
    material_passes = []
    vert_materials = []
    textures = []
    shaders = []

    @staticmethod
    def read(context, io_stream, chunk_end, type):
        result = PrelitBase(
            type=type,
            version=None,
            material_passes=[],
            vert_materials=[],
            textures=[],
            shaders=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_MATERIAL_INFO:
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
        return result


    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.mat_info.size()
        size += list_size(self.vert_materials)
        size += list_size(self.shaders)
        size += list_size(self.textures)
        size += list_size(self.material_passes, False)
        return size


    def write(self, io_stream):
        write_chunk_head(self.type, io_stream,
                         self.size(), has_sub_chunks=True)

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

        if self.material_passes:
            write_list(self.material_passes, io_stream,
                       MaterialPass.write)