# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.utils import *
from io_mesh_w3d.w3d.structs.version import Version


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
    def size(include_head=True):
        return const_size(44, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_HEADER, io_stream,
                         self.size(False))
        self.version.write(io_stream)
        write_fixed_string(self.name, io_stream)
        write_fixed_string(self.hierarchy_name, io_stream)
        write_ulong(self.num_frames, io_stream)
        write_ulong(self.frame_rate, io_stream)


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel(Struct):
    first_frame = 0
    last_frame = 0
    vector_len = 0
    type = 0
    pivot = 0
    unknown = 0
    data = []
    pad_bytes = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = AnimationChannel(
            first_frame=read_ushort(io_stream),
            last_frame=read_ushort(io_stream),
            vector_len=read_ushort(io_stream),
            type=read_ushort(io_stream),
            pivot=read_ushort(io_stream),
            unknown=read_ushort(io_stream),
            data=[],
            pad_bytes=[])

        num_elements = result.last_frame - result.first_frame + 1

        if result.vector_len == 1:
            result.data = read_fixed_list(io_stream, num_elements, read_float)
        else:
            result.data = read_fixed_list(
                io_stream, num_elements, read_quaternion)

        while io_stream.tell() < chunk_end:
            result.pad_bytes.append(read_ubyte(io_stream))
        return result

    def size(self, include_head=True):
        size = const_size(12, include_head)
        size += (len(self.data) * self.vector_len) * 4
        size += len(self.pad_bytes)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_CHANNEL, io_stream,
                         self.size(False))

        write_ushort(self.first_frame, io_stream)
        write_ushort(self.last_frame, io_stream)
        write_ushort(self.vector_len, io_stream)
        write_ushort(self.type, io_stream)
        write_ushort(self.pivot, io_stream)
        write_ushort(self.unknown, io_stream)

        if self.vector_len == 1:
            write_list(self.data, io_stream, write_float)
        else:
            write_list(self.data, io_stream, write_quaternion)
        write_list(self.pad_bytes, io_stream, write_ubyte)


W3D_CHUNK_ANIMATION_BIT_CHANNEL = 0x00000203


class AnimationBitChannel(Struct):
    first_frame = 0
    last_frame = 0
    type = 0
    pivot = 0
    default = False
    data = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = AnimationBitChannel(
            first_frame=read_ushort(io_stream),
            last_frame=read_ushort(io_stream),
            type=read_ushort(io_stream),
            pivot=read_ushort(io_stream),
            default=read_ubyte(io_stream))

        num_frames = result.last_frame - result.first_frame + 1
        result.data = [bool] * num_frames
        temp = 0
        for i in range(num_frames):
            if i % 8 == 0:
                temp = read_ubyte(io_stream)
            val = (temp & (1 << (i % 8))) != 0
            result.data[i] = val
        return result

    def size(self, include_head=True):
        size = const_size(9, include_head)
        size += (int)(len(self.data) / 8)
        if len(self.data) % 8 > 0:
            size += 1
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_BIT_CHANNEL, io_stream,
                         self.size(False))
        write_ushort(self.first_frame, io_stream)
        write_ushort(self.last_frame, io_stream)
        write_ushort(self.type, io_stream)
        write_ushort(self.pivot, io_stream)
        write_ubyte(self.default, io_stream)

        value = 0x00
        for i, datum in enumerate(self.data):
            if i > 0 and i % 8 == 0:
                write_ubyte(value, io_stream)
                value = 0x00
            value |= (int(datum) << (i % 8))
        write_ubyte(value, io_stream)


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
            elif chunk_type == W3D_CHUNK_ANIMATION_BIT_CHANNEL:
                result.channels.append(
                    AnimationBitChannel.read(io_stream, subchunk_end))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self):
        size = self.header.size()
        size += list_size(self.channels, False)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION, io_stream,
                         self.size(), has_sub_chunks=True)
        self.header.write(io_stream)

        for channel in self.channels:  # combination of animation and animationbit channels
            channel.write(io_stream)
