# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.rgba import RGBA
from io_mesh_w3d.w3d.utils.helpers import *

W3D_CHUNK_TEXTURE_STAGE = 0x00000048
W3D_CHUNK_TEXTURE_IDS = 0x00000049
W3D_CHUNK_STAGE_TEXCOORDS = 0x0000004A
W3D_CHUNK_PER_FACE_TEXCOORD_IDS = 0x0000004B


class TextureStage:
    def __init__(self, tx_ids=None, per_face_tx_coords=None, tx_coords=None):
        self.tx_ids = tx_ids if tx_ids is not None else []
        self.per_face_tx_coords = per_face_tx_coords if per_face_tx_coords is not None else []
        self.tx_coords = tx_coords if tx_coords is not None else []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = TextureStage()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_TEXTURE_IDS:
                result.tx_ids.append(read_list(io_stream, subchunk_end, read_long))
            elif chunk_type == W3D_CHUNK_STAGE_TEXCOORDS:
                result.tx_coords.append(read_list(io_stream, subchunk_end, read_vector2))
            elif chunk_type == W3D_CHUNK_PER_FACE_TEXCOORD_IDS:
                result.per_face_tx_coords.append(read_list(io_stream, subchunk_end, read_vector))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        for tx_id in self.tx_ids:
            size += long_list_size(tx_id)
        for tx_coord in self.tx_coords:
            size += vec2_list_size(tx_coord)
        for per_face_tx_coord in self.per_face_tx_coords:
            size += vec_list_size(per_face_tx_coord)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_TEXTURE_STAGE, io_stream,
                         self.size(False), has_sub_chunks=True)

        for tx_ids in self.tx_ids:
            write_chunk_head(W3D_CHUNK_TEXTURE_IDS, io_stream, long_list_size(tx_ids, False))
            write_list(tx_ids, io_stream, write_long)

        for tx_coords in self.tx_coords:
            write_chunk_head(W3D_CHUNK_STAGE_TEXCOORDS, io_stream, vec2_list_size(tx_coords, False))
            write_list(tx_coords, io_stream, write_vector2)

        for per_face_tx_coords in self.per_face_tx_coords:
            write_chunk_head(W3D_CHUNK_PER_FACE_TEXCOORD_IDS, io_stream, vec_list_size(per_face_tx_coords, False))
            write_list(per_face_tx_coords, io_stream, write_vector)


W3D_CHUNK_MATERIAL_PASS = 0x00000038
W3D_CHUNK_VERTEX_MATERIAL_IDS = 0x00000039
W3D_CHUNK_SHADER_IDS = 0x0000003A
W3D_CHUNK_DCG = 0x0000003B
W3D_CHUNK_DIG = 0x0000003C
W3D_CHUNK_SCG = 0x0000003E
W3D_CHUNK_SHADER_MATERIAL_ID = 0x0000003F


class MaterialPass:
    def __init__(self, vertex_material_ids=None, shader_ids=None, dcg=None, dig=None, scg=None,
                 shader_material_ids=None, tx_stages=None, tx_coords=None):
        self.vertex_material_ids = vertex_material_ids if vertex_material_ids is not None else []
        self.shader_ids = shader_ids if shader_ids is not None else []
        self.dcg = dcg if dcg is not None else []
        self.dig = dig if dig is not None else []
        self.scg = scg if scg is not None else []
        self.shader_material_ids = shader_material_ids if shader_material_ids is not None else []
        self.tx_stages = tx_stages if tx_stages is not None else []
        self.tx_coords = tx_coords if tx_coords is not None else []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = MaterialPass()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_VERTEX_MATERIAL_IDS:
                result.vertex_material_ids = read_list(io_stream, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_SHADER_IDS:
                result.shader_ids = read_list(io_stream, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_DCG:
                result.dcg = read_list(io_stream, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_DIG:
                result.dig = read_list(io_stream, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_SCG:
                result.scg = read_list(io_stream, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_ID:
                result.shader_material_ids = read_list(io_stream, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_TEXTURE_STAGE:
                result.tx_stages.append(TextureStage.read(context, io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_STAGE_TEXCOORDS:
                result.tx_coords = read_list(io_stream, subchunk_end, read_vector2)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += long_list_size(self.vertex_material_ids)
        size += long_list_size(self.shader_ids)
        size += list_size(self.dcg)
        size += list_size(self.dig)
        size += list_size(self.scg)
        size += long_list_size(self.shader_material_ids)
        size += list_size(self.tx_stages, False)
        size += vec2_list_size(self.tx_coords)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_MATERIAL_PASS, io_stream, self.size(False), has_sub_chunks=True)

        if self.vertex_material_ids:
            write_chunk_head(W3D_CHUNK_VERTEX_MATERIAL_IDS, io_stream,
                             long_list_size(self.vertex_material_ids, False))
            write_list(self.vertex_material_ids, io_stream, write_ulong)

        if self.shader_ids:
            write_chunk_head(W3D_CHUNK_SHADER_IDS, io_stream, long_list_size(self.shader_ids, False))
            write_list(self.shader_ids, io_stream, write_ulong)

        if self.dcg:
            write_chunk_head(W3D_CHUNK_DCG, io_stream, list_size(self.dcg, False))
            write_list(self.dcg, io_stream, RGBA.write)

        if self.dig:
            write_chunk_head(W3D_CHUNK_DIG, io_stream, list_size(self.dig, False))
            write_list(self.dig, io_stream, RGBA.write)

        if self.scg:
            write_chunk_head(W3D_CHUNK_SCG, io_stream, list_size(self.scg, False))
            write_list(self.scg, io_stream, RGBA.write)

        if self.shader_material_ids:
            write_chunk_head(W3D_CHUNK_SHADER_MATERIAL_ID, io_stream,
                             long_list_size(self.shader_material_ids, False))
            write_list(self.shader_material_ids, io_stream, write_ulong)

        write_list(self.tx_stages, io_stream, TextureStage.write)

        if self.tx_coords:
            write_chunk_head(W3D_CHUNK_STAGE_TEXCOORDS, io_stream,
                             vec2_list_size(self.tx_coords, False))
            write_list(self.tx_coords, io_stream, write_vector2)
