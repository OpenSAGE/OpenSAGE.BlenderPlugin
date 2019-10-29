# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.io_binary import *


W3D_CHUNK_ANIMATION_HEADER = 0x00000201


class AnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchy_name = ""
    num_frames = 0
    frame_rate = 0

    @staticmethod
    def read(io_stream):
        return AnimationHeader(
            version=Version.read(io_stream),
            name=read_fixed_string(io_stream),
            hierarchy_name=read_fixed_string(io_stream),
            num_frames=read_ulong(io_stream),
            frame_rate=read_ulong(io_stream))

    @staticmethod
    def size_in_bytes():
        return 44

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_ANIMATION_HEADER,
                         self.size_in_bytes())
        self.version.write(io_stream)
        write_fixed_string(io_stream, self.name)
        write_fixed_string(io_stream, self.hierarchy_name)
        write_ulong(io_stream, self.num_frames)
        write_ulong(io_stream, self.frame_rate)


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel(Struct):
    first_frame = 0
    last_frame = 0
    vector_len = 0
    type = 0
    pivot = 0
    unknown = 0
    data = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = AnimationChannel(
            first_frame=read_ushort(io_stream),
            last_frame=read_ushort(io_stream),
            vector_len=read_ushort(io_stream),
            type=read_ushort(io_stream),
            pivot=read_ushort(io_stream),
            unknown=read_ushort(io_stream),
            data=[])

        if result.vector_len == 1:
            result.data = read_array(io_stream, chunk_end, read_float)
        elif result.vector_len == 4:
            result.data = read_array(io_stream, chunk_end, read_quaternion)
        return result

    def size_in_bytes(self):
        return 12 + (len(self.data) * self.vector_len) * 4

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_ANIMATION_CHANNEL,
                         self.size_in_bytes())

        write_ushort(io_stream, self.first_frame)
        write_ushort(io_stream, self.last_frame)
        write_ushort(io_stream, self.vector_len)
        write_ushort(io_stream, self.type)
        write_ushort(io_stream, self.pivot)
        write_ushort(io_stream, self.unknown)

        if self.vector_len == 1:
            write_array(io_stream, self.data, write_float)
        else:
            write_array(io_stream, self.data, write_quaternion)


W3D_CHUNK_ANIMATION = 0x00000200


class Animation(Struct):
    header = AnimationHeader()
    channels = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Animation(channels=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_ANIMATION_HEADER:
                result.header = AnimationHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_ANIMATION_CHANNEL:
                result.channels.append(
                    AnimationChannel.read(io_stream, subchunk_end))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for channel in self.channels:
            size += HEAD + channel.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_ANIMATION,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)

        for channel in self.channels:
            channel.write(io_stream)
