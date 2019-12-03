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
    mat_info = MaterialInfo()
    material_passes = []
    vert_materials = []
    textures = []
    shaders = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = PrelitBase(
            version=None,
            material_passes=[],
            vert_materials=[],
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

    @staticmethod
    def size():
        size = list_size(self.shaders)
        size += list_size(self.textures)
        if self.mat_info is not None:
            size += self.mat_info.size()
        size += list_size(self.vert_materials)
        size += list_size(self.material_passes, False)
        return size

    def write(self, io_stream):
        #TODO: implementation
        pass
