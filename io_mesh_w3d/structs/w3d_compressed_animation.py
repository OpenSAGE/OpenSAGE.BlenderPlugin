# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct, HEAD
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.import_utils_w3d import read_fixed_array, skip_unknown_chunk
from io_mesh_w3d.io_binary import *


W3D_CHUNK_COMPRESSED_ANIMATION_HEADER = 0x00000281


class CompressedAnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchy_name = ""
    num_frames = 0
    frame_rate = 0
    flavor = 0

    @staticmethod
    def read(io_stream):
        return CompressedAnimationHeader(
            version=Version.read(io_stream),
            name=read_fixed_string(io_stream),
            hierarchy_name=read_fixed_string(io_stream),
            num_frames=read_ulong(io_stream),
            frame_rate=read_ushort(io_stream),
            flavor=read_ushort(io_stream))

    @staticmethod
    def size_in_bytes():
        return 44

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_COMPRESSED_ANIMATION_HEADER, self.size_in_bytes())
        self.version.write(io_stream)
        write_fixed_string(io_stream, self.name)
        write_fixed_string(io_stream, self.hierarchy_name)
        write_ulong(io_stream, self.num_frames)
        write_ushort(io_stream, self.frame_rate)
        write_ushort(io_stream, self.flavor)


class TimeCodedDatum(Struct):
    time_code = 0
    non_interpolated = False
    value = None

    @staticmethod
    def read(io_stream, type_):
        result = TimeCodedDatum(
            time_code=read_ulong(io_stream),
            value=read_channel_value(io_stream, type_))

        if (result.time_code >> 31) == 1:
            result.time_code &= ~(1 << 31)
            result.non_interpolated = True
        return result

    @staticmethod
    def size_in_bytes(type_):
        if type_ == 6:
            return 20
        return 8

    def write(self, io_stream, type_):
        time_code = self.time_code
        if self.non_interpolated:
            time_code |= (1 << 31)
        write_ulong(io_stream, time_code)
        write_channel_value(io_stream, type_, self.value)


class TimeCodedAnimationChannel(Struct):
    num_time_codes = 0
    pivot = -1
    vector_len = 0
    type = 0
    time_codes = []

    @staticmethod
    def read(io_stream):
        result = TimeCodedAnimationChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_ushort(io_stream),
            vector_len=read_ubyte(io_stream),
            type=read_ubyte(io_stream),
            time_codes=[])

        for _ in range(result.num_time_codes):
            result.time_codes.append(
                TimeCodedDatum.read(io_stream, result.type))
        return result

    def size_in_bytes(self):
        size = 8
        for time_code in self.time_codes:
            size += time_code.size_in_bytes(self.type)
        return size

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL, self.size_in_bytes())
        write_ulong(io_stream, self.num_time_codes)
        write_ushort(io_stream, self.pivot)
        write_ubyte(io_stream, self.vector_len)
        write_ubyte(io_stream, self.type)
        for time_code in self.time_codes:
            time_code.write(io_stream, self.type)


class AdaptiveDeltaBlock(Struct):
    vector_index = 0
    block_index = 0
    delta_bytes = []

    @staticmethod
    def read(io_stream, vec_index, bits):
        result = AdaptiveDeltaBlock(
            vector_index=vec_index,
            block_index=read_ubyte(io_stream),
            delta_bytes=[])

        result.delta_bytes = read_fixed_array(io_stream, bits * 2, read_byte)
        return result

    def size_in_bytes(self):
        return 1 + len(self.delta_bytes)

    def write(self, io_stream):
        write_ubyte(io_stream, self.block_index)
        write_array(io_stream, self.delta_bytes, write_byte)


class AdaptiveDeltaData(Struct):
    initial_value = None
    delta_blocks = []
    bit_count = 0

    @staticmethod
    def read(io_stream, channel, bits):
        result = AdaptiveDeltaData(
            initial_value=read_channel_value(io_stream, channel.type),
            delta_blocks=[],
            bit_count=bits)

        count = (channel.num_time_codes + 15) >> 4

        for _ in range(count):
            for j in range(channel.vector_len):
                result.delta_blocks.append(
                    AdaptiveDeltaBlock.read(io_stream, j, bits))
        return result

    def size_in_bytes(self, type_):
        size = 4
        if type_ == 6:
            size = 16
        for delta_block in self.delta_blocks:
            size += delta_block.size_in_bytes()
        return size

    def write(self, io_stream, type_):
        write_channel_value(io_stream, type_, self.initial_value)
        for delta_block in self.delta_blocks:
            delta_block.write(io_stream)


class AdaptiveDeltaAnimationChannel(Struct):
    num_time_codes = 0
    pivot = -1
    vector_len = 0
    type = 0
    scale = 0
    data = None

    @staticmethod
    def read(io_stream):
        result = AdaptiveDeltaAnimationChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_ushort(io_stream),
            vector_len=read_ubyte(io_stream),
            type=read_ubyte(io_stream),
            scale=read_short(io_stream),
            data=None)

        result.data = AdaptiveDeltaData.read(io_stream, result, 4)

        io_stream.read(3)  # read unknown bytes at the end
        return result

    def size_in_bytes(self):
        return 13 + self.data.size_in_bytes(self.type)

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL, self.size_in_bytes())
        write_ulong(io_stream, self.num_time_codes)
        write_ushort(io_stream, self.pivot)
        write_ubyte(io_stream, self.vector_len)
        write_ubyte(io_stream, self.type)
        write_short(io_stream, self.scale)
        self.data.write(io_stream, self.type)

        write_array(io_stream, bytes([0, 0, 0]), write_ubyte)  # padding


class AdaptiveDeltaMotionAnimationChannel(Struct):
    scale = 0.0
    initial_value = None
    data = None

    @staticmethod
    def read(io_stream, channel, bits):
        result = AdaptiveDeltaMotionAnimationChannel(
            scale=read_float(io_stream),
            data=[])

        result.data = AdaptiveDeltaData.read(io_stream, channel, bits)
        return result

    def size_in_bytes(self, type_):
        return 4 + self.data.size_in_bytes(type_)

    def write(self, io_stream, type_):
        write_float(io_stream, self.scale)
        self.data.write(io_stream, type_)


class TimeCodedBitDatum(Struct):
    time_code = 0
    value = None

    @staticmethod
    def read(io_stream):
        result = TimeCodedBitDatum(
            time_code=read_ulong(io_stream),
            value=False)

        if (result.time_code >> 31) == 1:
            result.value = True
            result.time_code &= ~(1 << 31)

        return result

    def size_in_bytes(self):
        return 4

    def write(self, io_stream):
        time_code = self.time_code
        if self.value:
            time_code |= (1 << 31)
        write_ulong(io_stream, time_code)


class TimeCodedBitChannel(Struct):
    num_time_codes = 0
    pivot = 0
    type = 0
    default_value = False
    time_codes = []

    @staticmethod
    def read(io_stream):
        result = TimeCodedBitChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_short(io_stream),
            type=read_ubyte(io_stream),
            default_value=read_ubyte(io_stream),
            time_codes=[])

        for _ in range(result.num_time_codes):
            result.time_codes.append(TimeCodedBitDatum.read(io_stream))
        return result

    def size_in_bytes(self):
        size = 8
        for time_code in self.time_codes:
            size += time_code.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_COMPRESSED_BIT_CHANNEL, self.size_in_bytes())
        write_ulong(io_stream, self.num_time_codes)
        write_ushort(io_stream, self.pivot)
        write_ubyte(io_stream, self.type)
        write_ubyte(io_stream, self.default_value)
        for time_code in self.time_codes:
            time_code.write(io_stream)


class MotionChannel(Struct):
    delta_type = 0
    vector_len = 0
    type = 0
    num_time_codes = 0
    pivot = 0
    data = []

    def read_time_coded_data(self, io_stream):
        result = []

        for _ in range(self.num_time_codes):
            datum = TimeCodedDatum(
                time_code=read_short(io_stream))
            result.append(datum)

        if self.num_time_codes % 2 != 0:
            read_short(io_stream)  # alignment

        for x in range(self.num_time_codes):
            result[x].value = read_channel_value(io_stream, self.type)
        return result

    def write_time_coded_data(self, io_stream):
        for datum in self.data:
            write_short(io_stream, datum.time_code)

        if self.num_time_codes % 2 != 0:
            write_short(io_stream, 0)  # alignment

        for datum in self.data:
            write_channel_value(io_stream, self.type, datum.value)

    @staticmethod
    def read(io_stream):
        read_ubyte(io_stream)  # zero

        result = MotionChannel(
            delta_type=read_ubyte(io_stream),
            vector_len=read_ubyte(io_stream),
            type=read_ubyte(io_stream),
            num_time_codes=read_short(io_stream),
            pivot=read_short(io_stream),
            data=[])

        if result.delta_type == 0:
            result.data = result.read_time_coded_data(io_stream)
        elif result.delta_type == 1:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(
                io_stream, result, 4)
        elif result.delta_type == 2:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(
                io_stream, result, 8)
        return result

    def size_in_bytes(self):
        size = 8
        if self.delta_type == 0:
            size += len(self.data) * 4
            if self.num_time_codes % 2 != 0:
                size += 2
        else:
            size += self.data.size_in_bytes(self.type)
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL,
                         self.size_in_bytes(), has_sub_chunks=True)
        write_ubyte(io_stream, 0)  # zero
        write_ubyte(io_stream, self.delta_type)
        write_ubyte(io_stream, self.vector_len)
        write_ubyte(io_stream, self.type)
        write_short(io_stream, self.num_time_codes)
        write_short(io_stream, self.pivot)

        if self.delta_type == 0:
            self.write_time_coded_data(io_stream)
        else:
            self.data.write(io_stream, self.type)


W3D_CHUNK_COMPRESSED_ANIMATION = 0x00000280
W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL = 0x00000282
W3D_CHUNK_COMPRESSED_BIT_CHANNEL = 0x00000283
W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL = 0x00000284


class CompressedAnimation(Struct):
    header = CompressedAnimationHeader()
    time_coded_channels = []
    adaptive_delta_channels = []
    time_coded_bit_channels = []
    motion_channels = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = CompressedAnimation(
            time_coded_channels=[],
            adaptive_delta_channels=[],
            time_coded_bit_channels=[],
            motion_channels=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, cE) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_HEADER:
                result.header = CompressedAnimationHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL:
                if result.header.flavor == 0:
                    result.time_coded_channels.append(
                        TimeCodedAnimationChannel.read(io_stream))
                elif result.header.flavor == 1:
                    result.adaptive_delta_channels.append(
                        AdaptiveDeltaAnimationChannel.read(io_stream))
                else:
                    skip_unknown_chunk(context, io_stream,
                                       chunk_type, chunk_size)
            elif chunk_type == W3D_CHUNK_COMPRESSED_BIT_CHANNEL:
                result.time_coded_bit_channels.append(
                    TimeCodedBitChannel.read(io_stream))
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL:
                result.motion_channels.append(
                    MotionChannel.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        if self.header.flavor == 0:
            for time_coded_channel in self.time_coded_channels:
                size += HEAD + time_coded_channel.size_in_bytes()
        elif self.header.flavor == 1:
            for adaptive_delta_channel in self.adaptive_delta_channels:
                size += HEAD + adaptive_delta_channel.size_in_bytes()
        for time_coded_bit_channel in self.time_coded_bit_channels:
            size += HEAD + time_coded_bit_channel.size_in_bytes()
        for motion_channel in self.motion_channels:
            size += HEAD + motion_channel.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_COMPRESSED_ANIMATION,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)
        if self.header.flavor == 0:
            for time_coded_channel in self.time_coded_channels:
                time_coded_channel.write(io_stream)
        elif self.header.flavor == 1:
            for adaptive_delta_channel in self.adaptive_delta_channels:
                adaptive_delta_channel.write(io_stream)
        for time_coded_bit_channel in self.time_coded_bit_channels:
            time_coded_bit_channel.write(io_stream)
        for motion_channel in self.motion_channels:
            motion_channel.write(io_stream)
